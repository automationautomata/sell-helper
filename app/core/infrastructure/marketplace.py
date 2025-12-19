import uuid
from dataclasses import asdict, dataclass
from typing import Optional

from app.core.infrastructure.common import EbayUtils
from pydantic import ValidationError
from shared.ebay_api import models as ebay_models
from shared.ebay_api.commerce import CommerceClientError, EbayCommerceClient
from shared.ebay_api.selling import EbaySellingClient, EbaySellingClientError
from shared.ebay_api.taxonomy import EbayTaxonomyClient, EbayTaxonomyClientError

from ...config import EbayConfig
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

    def publish(self, item: EbayItem, token: str, *images: str):
        try:
            images_urls = self._load_images(*images)
        except CommerceClientError as e:
            raise MarketplaceAPIError() from e

        try:
            sku = uuid.uuid4().hex.upper()[:50]
            utils = EbayUtils(self._taxonomy_api, token)
            dto = utils.get_category_id(item.category, self._config.marketplace_id)
            category_id = dto.category_id
        except EbaySellingClientError as e:
            raise MarketplaceAPIError() from e

        inventory_item = self._product_to_inventory_item(item, images_urls)
        try:
            self._selling_api.create_or_replace_inventory_item(sku, inventory_item)
        except EbaySellingClientError as e:
            self._publish_cleanup(token, sku)
            raise MarketplaceAPIError() from e

        try:
            offer = self._make_offer(sku, category_id, item.currency, item.price)
            offer_id = self._selling_api.create_offer(offer)

            self._selling_api.publish_offer(offer_id)
        except EbaySellingClientError as e:
            self._publish_cleanup(token, sku, offer_id)

            raise MarketplaceAPIError() from e

    def _load_images(self, token: str, *images: str):
        images_urls = []
        for img in images:
            img_response = self._commerce_api.upload_image(img, token)
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

    def _publish_cleanup(self, token: str, sku: str, offer_id: Optional[str] = None):
        try:
            self._selling_api.delete_inventory_item(sku, token)
            if offer_id:
                self._selling_api.delete_offer(offer_id, token)
        except EbaySellingClientError:
            pass

    def get_product_aspects(self, category_name: str, token: str) -> list[AspectType]:
        try:
            utils = EbayUtils(self._taxonomy_api, token)
            dto = utils.get_category_id(category_name, self._config.marketplace_id)
        except EbayTaxonomyClientError as e:
            raise MarketplaceAPIError from e

        if dto is None:
            raise CategoryNotExistsError(category_name)

        try:
            tree_id, category_id = dto.tree_id, category_id
            ebay_aspects = self._taxonomy_api.get_item_aspects(
                tree_id, category_id, token
            )
            return self._from_ebay_aspects(ebay_aspects)
        except EbayTaxonomyClientError as e:
            raise MarketplaceAPIError from e

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
