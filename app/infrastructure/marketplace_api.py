from dataclasses import asdict, dataclass
from typing import Generator

from pydantic import ValidationError

from ..domain.entities import AspectField, AspectType, Item
from ..services.ports import (
    CategoriesNotFoundError,
    MarketplaceAPIError,
)
from .api_clients.ebay import (
    EbayCommerceClient,
    EbayCommerceClientError,
    EbaySellingClient,
    EbaySellingClientError,
    EbayTaxonomyClient,
    EbayTaxonomyClientError,
)
from .api_clients.ebay import models as ebay_models
from .marketplace_aspects import EbayMarketplaceAspects


@dataclass
class EbayAPI:
    selling_api: EbaySellingClient
    taxonomy_api: EbayTaxonomyClient
    commerce_api: EbayCommerceClient
    sku_generator: Generator[str, None, None]

    def publish(self, item: Item[EbayMarketplaceAspects], token: str, *images: str):
        try:
            images_urls = self._load_images(*images)
        except EbayCommerceClientError as e:
            raise MarketplaceAPIError() from e

        sku = next(self.sku_generator)[:50]
        inventory_item = self._product_to_inventory_item(item, images_urls)

        try:
            _, category_id, _ = self._search_category(
                item.category, item.marketplace_aspects.marketplace
            )
            self.selling_api.create_or_replace_inventory_item(sku, inventory_item)
        except (EbayTaxonomyClientError, EbaySellingClientError) as e:
            self._publish_cleanup(token, sku)
            raise MarketplaceAPIError() from e

        offer = self._make_offer(
            sku, category_id, item.currency, item.price, item.marketplace_aspects
        )
        try:
            offer_id = self.selling_api.create_offer(offer)

            self.selling_api.publish_offer(offer_id)
        except (EbayTaxonomyClientError, EbaySellingClientError) as e:
            self._publish_cleanup(token, sku, offer_id)

            raise MarketplaceAPIError() from e

    def get_product_aspects(
        self, category_name: str, **marketplace_settings: dict
    ) -> list[AspectType]:
        marketplace_settings.get()
        try:
            search_res = self._search_category(category_name)
        except EbayTaxonomyClientError as e:
            raise MarketplaceAPIError from e

        if search_res is None:
            raise CategoriesNotFoundError(category_name)

        try:
            tree_id, category_id, _ = search_res
            ebay_aspects = self.taxonomy_api.get_item_aspects(tree_id, category_id)
            return self._from_ebay_aspects(ebay_aspects)
        except EbayTaxonomyClientError as e:
            raise MarketplaceAPIError from e

    def _load_images(self, token: str, *images: str):
        images_urls = []
        for img in images:
            img_response = self.commerce_api.upload_image(img, token)
            images_urls.append(img_response.image_url)
        return images_urls

    def _make_offer(
        self,
        sku: str,
        category_id: str,
        currency: str,
        price: float,
        marketplace_aspects: EbayMarketplaceAspects,
    ):
        price = ebay_models.Price(currency=currency, value=price)

        policies = ebay_models.ListingPolicies(
            fulfillment_policy_id=marketplace_aspects.policies.fulfillment_policy_id,
            payment_policy_id=marketplace_aspects.policies.payment_policy_id,
            return_policy_id=marketplace_aspects.policies.return_policy_id,
        )

        marketplace_id = marketplace_aspects.marketplace
        location_key = marketplace_aspects.location_key

        return ebay_models.Offer(
            sku=sku,
            format="FIXED_PRICE",
            category_id=category_id,
            marketplace_id=marketplace_id,
            listing_policies=policies,
            pricing_summary=ebay_models.PricingSummary(price=price),
            merchant_location_key=location_key,
        )

    def _publish_cleanup(self, token: str, sku: str, offer_id: str | None = None):
        try:
            self.selling_api.delete_inventory_item(sku, token)
            if offer_id:
                self.selling_api.delete_offer(offer_id, token)
        except EbaySellingClientError:
            pass

    @classmethod
    def _from_ebay_aspects(
        cls, ebay_aspects: ebay_models.AspectMetadata
    ) -> list[AspectType]:
        def type_mapping(constraint):
            cardinality = constraint.item_to_aspect_cardinality
            if cardinality == ebay_models.ItemToAspectCardinalityEnum.MULTI:
                return AspectType.LIST

            mapping = {
                ebay_models.AspectValueTypeEnum.STRING: AspectType.STR,
                ebay_models.AspectValueTypeEnum.STRING_ARRAY: AspectType.STR,
                ebay_models.AspectValueTypeEnum.NUMBER: AspectType.FLOAT,
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
    def _product_to_inventory_item(
        item: Item[EbayMarketplaceAspects],
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
        for aspect in item.product_aspects.aspects:
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

    def _search_category(
        self, category_name: str, marketplace_id: str
    ) -> tuple[str, str, str] | None:
        tree_id = self.taxonomy_api.get_default_tree_id(marketplace_id)
        tree = self.taxonomy_api.fetch_category_tree(tree_id)
        res = self._search_in_tree(tree, category_name)
        if res is None:
            return None

        category_id, category_name = res
        return tree_id, category_id, category_name

    @staticmethod
    def _search_in_tree(
        tree: ebay_models.CategoryTree, target: str
    ) -> tuple[str, str] | None:
        """Recursively search the node and its children for categoryName matches
        and returns categoryId and categoryName."""

        def search(node) -> tuple[str, str] | None:
            if node.leaf_category_tree_node:
                category = node.category
                name = category.category_name

                if name and target.lower() == name.lower():
                    return category.category_id, name

            for child in node.child_category_tree_nodes:
                res = search(child)
                if res:
                    return res

            return None

        return search(tree.root_category_node)
