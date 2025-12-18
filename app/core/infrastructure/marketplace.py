import uuid
from dataclasses import asdict, dataclass
from typing import Optional

from pydantic import ValidationError

from ...config import EbayConfig
from ...external.ebay import models as ebay_models
from ...external.ebay.commerce import CommerceClientError, EbayCommerceClient
from ...external.ebay.selling import EbaySellingClient, EbaySellingClientError
from ...external.ebay.taxonomy import EbayTaxonomyClient, EbayTaxonomyClientError
from ..domain.entities.ebay.item import EbayItem
from ..domain.entities.value_objects import AspectField, AspectType
from ..services.ports import CategoryNotExistsError, MarketplaceAPIError


@dataclass
class EbayClients:
    selling_client: EbaySellingClient
    taxonomy_client: EbayTaxonomyClient
    commerce_client: EbayCommerceClient


class EbayAPI:
    def __init__(self, config: EbayConfig, clients: EbayClients):
        self._config = config

        self._selling_api = clients.selling_client
        self._taxonomy_api = clients.taxonomy_client
        self._commerce_api = clients.commerce_client

    def publish(self, item: EbayItem, *images: str):
        try:
            images_urls = self._load_images(*images)
        except CommerceClientError as e:
            raise MarketplaceAPIError() from e

        try:
            sku = uuid.uuid4().hex.upper()[:50]
            category_id, _ = self.get_category_id(item.category)
        except EbaySellingClientError as e:
            raise MarketplaceAPIError() from e

        inventory_item = self._product_to_inventory_item(item, images_urls)
        try:
            self._selling_api.create_or_replace_inventory_item(sku, inventory_item)
        except EbaySellingClientError as e:
            self._publish_cleanup(sku)

            raise MarketplaceAPIError() from e

        try:
            offer = self._make_offer(sku, category_id, item.currency, item.price)
            offer_id = self._selling_api.create_offer(offer)

            self._selling_api.publish_offer(offer_id)
        except EbaySellingClientError as e:
            self._publish_cleanup(sku, offer_id)

            raise MarketplaceAPIError() from e

    def _load_images(self, *images: str):
        images_urls = []
        for img in images:
            img_response = self._commerce_api.upload_image(img)
            images_urls.append(img_response.image_url)
        return images_urls

    def _make_offer(self, sku: str, category_id: str, currency: str, price: float):
        marketplace_id = self._config.marketplace_id
        price = ebay_models.Price(currency=currency, value=price)

        return ebay_models.Offer(
            sku=sku,
            format="FIXED_PRICE",
            category_id=category_id,
            marketplace_id=marketplace_id,
            listing_policies=self._get_listing_policies(),
            pricing_summary=ebay_models.PricingSummary(price=price),
            merchant_location_key=self._config.location_key,
        )

    def _get_listing_policies(self):
        listing_policies = self._config.listing_policies

        fulfillment_policy_id = listing_policies.fulfillment_policy_id
        payment_policy_id = listing_policies.payment_policy_id
        return_policy_id = listing_policies.return_policy_id

        return ebay_models.ListingPolicies(
            fulfillmentPolicyId=fulfillment_policy_id,
            paymentPolicyId=payment_policy_id,
            returnPolicyId=return_policy_id,
        )

    def _publish_cleanup(self, sku: str, offer_id: Optional[str] = None):
        try:
            self._selling_api.delete_inventory_item(sku)
            if offer_id:
                self._selling_api.delete_offer(offer_id)
        except EbaySellingClientError:
            pass

    def get_category_id(self, category_name: str) -> tuple[str, str]:
        try:
            _, tree = self._get_category_tree()
        except EbayTaxonomyClientError as e:
            raise MarketplaceAPIError from e

        res = self._search_category(tree, category_name)
        if res is None:
            raise CategoryNotExistsError(f"Category '{category_name}' not found")

        id, name = res
        return id, name

    def get_product_aspects(self, category_name: str) -> list[AspectType]:
        try:
            tree_id, tree = self._get_category_tree()
        except EbayTaxonomyClientError as e:
            raise MarketplaceAPIError from e

        res = self._search_category(tree, category_name)
        if res is None:
            raise CategoryNotExistsError(f"Category '{category_name}' not found")

        try:
            id, _ = res
            ebay_aspects = self._taxonomy_api.get_item_aspects(tree_id, id)
            return self._from_ebay_aspects(ebay_aspects)
        except EbayTaxonomyClientError as e:
            raise MarketplaceAPIError from e

    def _get_category_tree(self) -> tuple[str, ebay_models.CategoryTree]:
        tree_id = self._taxonomy_api.get_default_tree_id(self._config.marketplace_id)
        tree = self._taxonomy_api.fetch_category_tree(tree_id)
        return tree_id, tree

    @classmethod
    def _from_ebay_aspects(
        cls, ebay_aspects: ebay_models.AspectMetadata
    ) -> list[AspectType]:
        def type_mapping(constraint):
            cardinality = constraint.item_to_aspect_cardinality
            if cardinality == ebay_models.ItemToAspectCardinalityEnum.MULTI:
                return AspectType.LIST

            mapping = {
                ebay_models.AspectDataTypeEnum.STRING: AspectType.STR,
                ebay_models.AspectDataTypeEnum.STRING_ARRAY: AspectType.STR,
                ebay_models.AspectDataTypeEnum.NUMBER: AspectType.FLOAT,
            }
            return mapping.get(constraint.aspect_data_type, AspectType.STR)

        RECOMMENDED = ebay_models.AspectUsageEnum.RECOMMENDED
        SELECTION_ONLY = ebay_models.AspectModeEnum.SELECTION_ONLY

        aspects = []
        for aspect in ebay_aspects.aspects:
            constraint = aspect.aspect_constraint
            is_required = constraint.aspect_required
            is_recomended_mode = constraint.aspect_usage == RECOMMENDED

            allowed_values = set()
            if constraint.aspect_mode == SELECTION_ONLY:
                allowed_values.update(v.localized_value for v in aspect.aspect_values)

            name = aspect.localized_aspect_name
            data_type = type_mapping(constraint)

            aspects.append(
                AspectField(
                    name=name,
                    data_type=data_type,
                    is_required=is_recomended_mode or is_required,
                    allowed_values=frozenset(allowed_values),
                )
            )

        return aspects

    @staticmethod
    def _search_category(
        tree: ebay_models.CategoryTree, target: str
    ) -> tuple[str, str] | None:
        """Recursively search the node and its children for categoryName matches
        and returns categoryId and categoryName."""

        def search(n: ebay_models.CategoryTreeNode) -> tuple[str, str] | None:
            if n.leaf_category_tree_node:
                category = n.category
                name = category.category_name

                if name and target.lower() == name.lower():
                    return category.category_id, name

            for child in n.child_category_tree_nodes:
                res = search(child)
                if res:
                    return res

            return None

        return search(tree.root_category_node)

    @staticmethod
    def _product_to_inventory_item(
        item: EbayItem,
        images_urls: list[str],
        *,
        is_shipping: bool = True,
    ) -> ebay_models.InventoryItem:
        """
        Convert a Item[EbayProduct, EbayMarketplaceAspects] to an eBay Sell API InventoryItem.
        """
        availability = ebay_models.Availability(
            ship_to_location_availability=ebay_models.ShipToLocationAvailability(
                quantity=item.quantity
            )
        )

        ebay_aspects = {}
        for aspect in item.product.aspects:
            value = aspect.value
            if value:
                if not isinstance(value, list):
                    value = [value]
                ebay_aspects[aspect.name] = list(map(str, value))

        ebay_product = ebay_models.Product(
            title=item.title,
            aspects=ebay_aspects,
            image_urls=images_urls,
            description=item.description,
        )

        marketplace_aspects = item.marketplace_aspects

        package = None
        if is_shipping:
            package = ebay_models.PackageWeightAndSize(
                **asdict(marketplace_aspects.package)
            )

        condition = marketplace_aspects.condition
        condition_description = marketplace_aspects.condition_description
        try:
            return ebay_models.InventoryItem(
                availability=availability,
                condition=condition,
                product=ebay_product,
                package_weight_and_size=package,
                condition_description=condition_description,
            )
        except ValidationError as e:
            raise MarketplaceAPIError() from e
