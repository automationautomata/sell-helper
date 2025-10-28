from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, alias_generators

# --- ENUMS ---


class MarketplaceIdEnum(str, Enum):
    EBAY_AU = "EBAY_AU"
    EBAY_AT = "EBAY_AT"
    EBAY_BE = "EBAY_BE"
    EBAY_CA = "EBAY_CA"
    EBAY_FR = "EBAY_FR"
    EBAY_DE = "EBAY_DE"
    EBAY_HK = "EBAY_HK"
    EBAY_IE = "EBAY_IE"
    EBAY_IT = "EBAY_IT"
    EBAY_MY = "EBAY_MY"
    EBAY_NL = "EBAY_NL"
    EBAY_PH = "EBAY_PH"
    EBAY_PL = "EBAY_PL"
    EBAY_RU = "EBAY_RU"
    EBAY_SG = "EBAY_SG"
    EBAY_ES = "EBAY_ES"
    EBAY_CH = "EBAY_CH"
    EBAY_GB = "EBAY_GB"
    EBAY_US = "EBAY_US"
    EBAY_MOTORS = "EBAY_MOTORS"


class ConditionEnum(str, Enum):
    NEW = "NEW"
    LIKE_NEW = "LIKE_NEW"
    NEW_OTHER = "NEW_OTHER"
    USED_EXCELLENT = "USED_EXCELLENT"
    USED_GOOD = "USED_GOOD"
    USED_ACCEPTABLE = "USED_ACCEPTABLE"
    FOR_PARTS_OR_NOT_WORKING = "FOR_PARTS_OR_NOT_WORKING"


class AvailabilityTypeEnum(str, Enum):
    IN_STOCK = "IN_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    SHIP_TO_STORE = "SHIP_TO_STORE"


class LengthUnitOfMeasureEnum(str, Enum):
    INCH = "INCH"
    FEET = "FEET"
    CENTIMETER = "CENTIMETER"
    METER = "METER"


class WeightUnitOfMeasureEnum(str, Enum):
    POUND = "POUND"
    KILOGRAM = "KILOGRAM"
    OUNCE = "OUNCE"
    GRAM = "GRAM"


# --- BASE MODEL ---


class EbayModel(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True,
        alias_generator=alias_generators.to_camel,
    )


# --- SUBMODELS ---


class Weight(EbayModel):
    unit: WeightUnitOfMeasureEnum
    value: float


class Dimension(EbayModel):
    height: float
    length: float
    width: float
    unit: LengthUnitOfMeasureEnum


class PackageWeightAndSize(EbayModel):
    weight: Weight
    dimensions: Optional[Dimension] = None


class PickupAtLocationAvailability(EbayModel):
    availability_type: AvailabilityTypeEnum
    merchant_location_key: str
    quantity: int


class ShipToLocationAvailability(EbayModel):
    quantity: int


class Availability(EbayModel):
    ship_to_location_availability: Optional[ShipToLocationAvailability] = None
    pickup_at_location_availability: Optional[List[PickupAtLocationAvailability]] = None


class NameValuePair(EbayModel):
    name: str
    value: List[str] = Field(default_factory=list)


class ItemAspects(EbayModel):
    name_value_list: List[NameValuePair] = Field(default_factory=list)


class Product(EbayModel):
    title: str
    description: str
    brand: Optional[str] = None
    image_urls: Optional[List[str]] = None
    aspects: Optional[dict[str, list[str]]] = None


class InventoryItem(EbayModel):
    """eBay InventoryItem model (Sell Inventory API)."""

    availability: Availability
    condition: ConditionEnum
    condition_description: Optional[str] = None
    product: Product
    package_weight_and_size: Optional[PackageWeightAndSize] = None


# --- OFFER MODELS ---


class ListingPolicies(EbayModel):
    fulfillment_policy_id: str
    payment_policy_id: str
    return_policy_id: str


class Price(EbayModel):
    currency: str
    value: float


class PricingSummary(EbayModel):
    price: Price


class Offer(EbayModel):
    sku: str
    format: Literal["AUCTION", "FIXED_PRICE"]
    category_id: str
    marketplace_id: MarketplaceIdEnum
    listing_policies: ListingPolicies
    pricing_summary: PricingSummary
    merchant_location_key: str


# --- TOKEN RESPONSE ---


class RefreshTokenResponse(EbayModel):
    access_token: str
    expires_in: int
    token_type: str


# --- TAXONOMY MODELS ---


class AspectApplicableToEnum(str, Enum):
    ITEM = "ITEM"
    PRODUCT = "PRODUCT"


class AspectDataTypeEnum(str, Enum):
    DATE = "DATE"
    NUMBER = "NUMBER"
    STRING = "STRING"
    STRING_ARRAY = "STRING_ARRAY"


class AspectModeEnum(str, Enum):
    FREE_TEXT = "FREE_TEXT"
    SELECTION_ONLY = "SELECTION_ONLY"


class AspectUsageEnum(str, Enum):
    RECOMMENDED = "RECOMMENDED"
    OPTIONAL = "OPTIONAL"


class ItemToAspectCardinalityEnum(str, Enum):
    MULTI = "MULTI"
    SINGLE = "SINGLE"


class AspectAdvancedDataTypeEnum(str, Enum):
    NUMERIC_RANGE = "NUMERIC_RANGE"


class ValueConstraint(EbayModel):
    applicable_for_localized_aspect_name: str
    applicable_for_localized_aspect_values: list[str]


class AspectValue(EbayModel):
    localized_value: str
    value_constraints: list[ValueConstraint] = Field(default_factory=list)


class RelevanceIndicator(EbayModel):
    search_count: int


class AspectConstraint(EbayModel):
    aspect_applicable_to: list[AspectApplicableToEnum] = Field(default_factory=list)
    aspect_data_type: AspectDataTypeEnum
    aspect_enabled_for_variations: bool
    aspect_format: str | None = None
    aspect_max_length: int | None = None
    aspect_mode: AspectModeEnum
    aspect_required: bool
    aspect_usage: AspectUsageEnum
    expected_required_by_date: str | None = None
    item_to_aspect_cardinality: ItemToAspectCardinalityEnum
    aspect_advanced_data_type: AspectAdvancedDataTypeEnum | None = None


class Aspect(EbayModel):
    aspect_constraint: AspectConstraint
    aspect_values: list[AspectValue] = Field(default_factory=list)
    localized_aspect_name: str
    relevance_indicator: RelevanceIndicator | None = None


class AspectMetadata(EbayModel):
    aspects: list[Aspect]


class Category(EbayModel):
    category_id: str
    category_name: str


class CategoryTreeNode(EbayModel):
    category: Category
    category_tree_node_level: int
    child_category_tree_nodes: list["CategoryTreeNode"] = Field(default_factory=list)
    leaf_category_tree_node: Optional[bool] = None
    parent_category_tree_node_href: Optional[str] = None


class CategoryTree(EbayModel):
    applicable_marketplace_ids: list[MarketplaceIdEnum]
    category_tree_id: str
    category_tree_version: str
    root_category_node: CategoryTreeNode


CategoryTreeNode.model_rebuild()  # Update forward refs


class CategoryTreeNodeAncestor(EbayModel):
    category_id: str
    category_name: str
    category_subtree_node_href: str
    category_tree_node_level: int


class CategorySuggestion(EbayModel):
    category: Category
    category_tree_node_ancestors: List[CategoryTreeNodeAncestor]
    category_tree_node_level: int


class CategorySuggestionResponse(EbayModel):
    category_suggestions: List[CategorySuggestion]
    category_tree_id: str
    category_tree_version: str


class ImageResponse(EbayModel):
    expiration_date: str
    image_url: str
