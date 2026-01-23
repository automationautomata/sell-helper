from collections.abc import Generator
from dataclasses import asdict, dataclass

from pydantic import ValidationError

from app.domain.entities import AspectField, AspectType, Item
from app.domain.entities.account import AccountSettings
from app.services.ports import (
    CategoriesNotFoundError,
    MarketplaceAPIError,
)
from app.services.ports.errors import AccountSettingsNotFound

from .api_clients.ebay import (
    EbayAccountClient,
    EbayAccountClientError,
    EbayCommerceClient,
    EbayCommerceClientError,
    EbaySellingClient,
    EbaySellingClientError,
    EbayTaxonomyClient,
    EbayTaxonomyClientError,
)
from .api_clients.ebay import models as ebay_models
from .marketplace_aspects import EbayAspects, EbayPolicies


@dataclass
class EbayAPI:
    selling_api: EbaySellingClient
    taxonomy_api: EbayTaxonomyClient
    commerce_api: EbayCommerceClient
    account_api: EbayAccountClient
    sku_generator: Generator[str, None, None]

    def publish(self, item: Item[EbayAspects], token: str, *images: str):
        sku = next(self.sku_generator)[:50]

        try:
            images_urls = self._load_images(*images)
            inventory_item = self._to_inventory_item(item, images_urls)

            _, category_id, _ = self._search_category(
                item.category, item.marketplace_aspects.marketplace
            )

            self.selling_api.create_or_replace_inventory_item(sku, inventory_item)
        except (EbayCommerceClientError, EbaySellingClientError) as e:
            self._publish_cleanup(token, sku)
            raise MarketplaceAPIError() from e

        offer_id = None
        marketplace_aspects = item.marketplace_aspects
        try:
            res = self._get_policeis_ids(marketplace_aspects.policies)
            if res is not None:
                raise AccountSettingsNotFound()
            fulfillment_id, payment_id, return_id = res

            location_key = self._get_location_key(marketplace_aspects.location)
            if res is not None:
                raise AccountSettingsNotFound()

            offer = self._create_offer(
                sku,
                category_id,
                item.currency,
                item.price,
                fulfillment_id,
                payment_id,
                return_id,
                location_key,
            )
            offer_id = self.selling_api.create_offer(offer)

            self.selling_api.publish_offer(offer_id)

        except (EbaySellingClientError, EbayAccountClientError) as e:
            self._publish_cleanup(token, sku, offer_id)

            raise MarketplaceAPIError() from e

        except AccountSettingsNotFound:
            raise

    def _publish_cleanup(self, token: str, sku: str, offer_id: str | None = None):
        try:
            self.selling_api.delete_inventory_item(sku, token)
            if offer_id:
                self.selling_api.delete_offer(offer_id, token)
        except EbaySellingClientError:
            pass

    def get_product_aspects(
        self, category_name: str, *, marketplace_id: str
    ) -> list[AspectType]:
        try:
            search_res = self._search_category(category_name, marketplace_id)

            if search_res is None:
                raise CategoriesNotFoundError(category_name)

            tree_id, category_id, _ = search_res
            ebay_aspects = self.taxonomy_api.get_item_aspects(tree_id, category_id)
            return self._from_ebay_aspects(ebay_aspects)

        except EbayTaxonomyClientError as e:
            raise MarketplaceAPIError from e
        except CategoriesNotFoundError:
            raise

    def get_account_settings(self, token: str) -> AccountSettings:
        def get_names(items):
            return [it.name for it in items]

        policies = self.account_api.get_all_policies(token)

        return AccountSettings(
            dict(
                fulfillment_policies=get_names(policies["fulfillment_policies"]),
                payment_policies=get_names(policies["payment_policies"]),
                return_policies=get_names(policies["return_policies"]),
                locations=get_names(self.selling_api.get_locations(token)),
            )
        )

    def _load_images(self, token: str, *images: str):
        images_urls = []
        for img in images:
            img_response = self.commerce_api.upload_image(img, token)
            images_urls.append(img_response.image_url)
        return images_urls

    def _get_location_key(self, location_name: str) -> str:
        locations = self.selling_api.get_locations()
        for location in locations:
            if location["name"].lower() == location_name.lower():
                return location_name

    def _get_policeis_ids(
        self, ebay_policies: EbayPolicies, token: str
    ) -> tuple[str, str, str] | None:
        def find(policies, src_name):
            for policy in policies:
                if policy["name"].lower() == src_name.lower():
                    return policy.id

        policies = self.account_api.get_all_policies(token)

        fulfillment_id = find(
            policies.fulfillment_policies, ebay_policies.fulfillment_policy
        )
        payment_id = find(policies.payment_policies, ebay_policies.payment_policy)
        return_id = find(policies.return_policies, ebay_policies.return_policy)

        if not (fulfillment_id and payment_id and return_id):
            return None

        return fulfillment_id, payment_id, return_id

    def _create_offer(
        self,
        sku: str,
        category_id: str,
        currency: str,
        price: float,
        marketplace: str,
        fulfillment_policy_id: str,
        payment_policy_id: str,
        return_policy_id: str,
        location_key: str,
    ):
        price = ebay_models.Price(currency=currency, value=price)

        policies = ebay_models.ListingPolicies(
            fulfillment_policy_id=fulfillment_policy_id,
            payment_policy_id=payment_policy_id,
            return_policy_id=return_policy_id,
        )

        marketplace_id = marketplace
        return ebay_models.Offer(
            sku=sku,
            format="FIXED_PRICE",
            category_id=category_id,
            marketplace_id=marketplace_id,
            listing_policies=policies,
            pricing_summary=ebay_models.PricingSummary(price=price),
            merchant_location_key=location_key,
        )

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
    def _to_inventory_item(
        item: Item[EbayAspects],
        images_urls: list[str],
        *,
        is_shipping: bool = True,
    ) -> ebay_models.InventoryItem:
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
