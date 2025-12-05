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

    product: Product
    condition: ConditionEnum
    availability: Availability
    package_weight_and_size: PackageWeightAndSize
    condition_description: Optional[str] = None


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


class UploadImageResponse(EbayModel):
    expiration_date: str
    image_url: str


# ------------------------------------------------------
# Enums
# ------------------------------------------------------


class CompatibilityMatchEnum(str, Enum):
    EXACT = "EXACT"
    POSSIBLE = "POSSIBLE"


class PriceTreatmentEnum(str, Enum):
    MINIMUM_ADVERTISED_PRICE = "MINIMUM_ADVERTISED_PRICE"
    LIST_PRICE = "LIST_PRICE"
    MARKDOWN = "MARKDOWN"


class PriceDisplayConditionEnum(str, Enum):
    ONLY_SHOW_WHEN_ADDED_IN_CART = "ONLY_SHOW_WHEN_ADDED_IN_CART"
    ONLY_SHOW_ON_REQUEST = "ONLY_SHOW_ON_REQUEST"
    ALWAYS_SHOW = "ALWAYS_SHOW"


class Image(EbayModel):
    height: Optional[int] = None
    image_url: Optional[str] = None
    width: Optional[int] = None


class ItemSummaryPrice(EbayModel):
    converted_from_currency: Optional[str] = None
    converted_from_value: Optional[str] = None
    currency: Optional[str] = None
    value: Optional[str] = None


class Category(EbayModel):
    category_id: Optional[str] = None
    category_name: Optional[str] = None


class CompatibilityProperty(EbayModel):
    localized_name: Optional[str] = None
    name: Optional[str] = None
    value: Optional[str] = None


class Address(EbayModel):
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    county: Optional[str] = None
    postal_code: Optional[str] = None
    state_or_province: Optional[str] = None


class ShippingCost(EbayModel):
    converted_from_currency: Optional[str] = None
    converted_from_value: Optional[str] = None
    currency: Optional[str] = None
    value: Optional[str] = None


class ShippingOption(EbayModel):
    guaranteed_delivery: Optional[bool] = None
    max_estimated_delivery_date: Optional[str] = None
    min_estimated_delivery_date: Optional[str] = None
    shipping_cost: Optional[ShippingCost] = None
    shipping_cost_type: Optional[str] = None


class Seller(EbayModel):
    feedback_percentage: Optional[str] = None
    feedback_score: Optional[int] = None
    seller_account_type: Optional[str] = None
    username: Optional[str] = None


# ------------------------------------------------------
# Marketing Price
# ------------------------------------------------------


class MarketingPrice(EbayModel):
    discount_amount: Optional[ItemSummaryPrice] = None
    discount_percentage: Optional[str] = None
    original_price: Optional[ItemSummaryPrice] = None
    price_treatment: Optional[PriceTreatmentEnum] = None


# ------------------------------------------------------
# Item Summary
# ------------------------------------------------------


class ItemSummary(EbayModel):
    additional_images: Optional[List[Image]] = None
    adult_only: Optional[bool] = None
    available_coupons: Optional[bool] = None
    bid_count: Optional[int] = None
    buying_options: Optional[List[str]] = None
    categories: Optional[List[Category]] = None
    compatibility_match: Optional[CompatibilityMatchEnum] = None
    compatibility_properties: Optional[List[CompatibilityProperty]] = None
    condition: Optional[str] = None
    condition_id: Optional[str] = None
    current_bid_price: Optional[ItemSummaryPrice] = None
    distance_from_pickup_location: Optional[dict] = None
    energy_efficiency_class: Optional[str] = None
    epid: Optional[str] = None
    image: Optional[Image] = None
    item_affiliate_web_url: Optional[str] = None
    item_creation_date: Optional[str] = None
    item_end_date: Optional[str] = None
    item_group_href: Optional[str] = None
    item_group_type: Optional[str] = None
    item_href: Optional[str] = None
    item_id: Optional[str] = None
    item_location: Optional[Address] = None
    item_origin_date: Optional[str] = None
    item_web_url: Optional[str] = None
    leaf_category_ids: Optional[List[str]] = None
    legacy_item_id: Optional[str] = None
    listing_marketplace_id: Optional[MarketplaceIdEnum] = None
    marketing_price: Optional[MarketingPrice] = None
    pickup_options: Optional[List[dict]] = None
    price: Optional[ItemSummaryPrice] = None
    price_display_condition: Optional[PriceDisplayConditionEnum] = None
    priority_listing: Optional[bool] = None
    qualified_programs: Optional[List[str]] = None
    seller: Optional[Seller] = None
    shipping_options: Optional[List[ShippingOption]] = None
    short_description: Optional[str] = None
    thumbnail_images: Optional[List[Image]] = None
    title: Optional[str] = None
    top_rated_buying_experience: Optional[bool] = None
    tyre_label_image_url: Optional[str] = None
    unit_price: Optional[ItemSummaryPrice] = None
    unit_pricing_measure: Optional[str] = None
    watch_count: Optional[int] = None


# ------------------------------------------------------
# Refinement
# ------------------------------------------------------


class AspectValueDistribution(EbayModel):
    localized_aspect_value: Optional[str] = None
    match_count: Optional[int] = None
    refinement_href: Optional[str] = None


class AspectDistribution(EbayModel):
    localized_aspect_name: Optional[str] = None
    aspect_value_distributions: Optional[List[AspectValueDistribution]] = None


class BuyingOptionDistribution(EbayModel):
    buying_option: Optional[str] = None
    match_count: Optional[int] = None
    refinement_href: Optional[str] = None


class ConditionDistribution(EbayModel):
    condition: Optional[str] = None
    condition_id: Optional[str] = None
    match_count: Optional[int] = None
    refinement_href: Optional[str] = None


class Refinement(EbayModel):
    aspect_distributions: Optional[List[AspectDistribution]] = None
    buying_option_distributions: Optional[List[BuyingOptionDistribution]] = None
    category_distributions: Optional[List[Category]] = None
    condition_distributions: Optional[List[ConditionDistribution]] = None
    dominant_category_id: Optional[str] = None


# ------------------------------------------------------
# Warning
# ------------------------------------------------------


class ErrorParameter(EbayModel):
    name: Optional[str] = None
    value: Optional[str] = None


class Warning(EbayModel):
    category: Optional[str] = None
    domain: Optional[str] = None
    error_id: Optional[int] = None
    input_ref_ids: Optional[List[str]] = None
    long_message: Optional[str] = None
    message: Optional[str] = None
    output_ref_ids: Optional[List[str]] = None
    parameters: Optional[List[ErrorParameter]] = None
    subdomain: Optional[str] = None


# ------------------------------------------------------
# Root Response
# ------------------------------------------------------


class EbaySearchResponse(EbayModel):
    auto_corrections: Optional[dict] = None
    href: Optional[str] = None
    item_summaries: Optional[List[ItemSummary]] = None
    limit: Optional[int] = None
    next: Optional[str] = None
    offset: Optional[int] = None
    prev: Optional[str] = None
    refinement: Optional[Refinement] = None
    total: Optional[int] = None
    warnings: Optional[List[Warning]] = None
