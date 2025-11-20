from unittest.mock import Mock

import pytest
from app.config import EbayConfig
from app.core.domain.ebay.item import EbayItem, EbayMarketplaceAspects
from app.core.domain.ebay.value_objects import Dimension, Package, Weight
from app.core.domain.value_objects import AspectData, AspectType
from app.core.infrastructure.marketplace import (
    CategoryNotExistsError,
    EbayAPI,
    EbayClients,
    MarketplaceAPIError,
)
from app.external.ebay import models as ebay_models
from app.external.ebay.commerce import CommerceClientError, EbayCommerceClient
from app.external.ebay.selling import EbaySellingClient
from app.external.ebay.taxonomy import EbayTaxonomyClient, EbayTaxonomyClientError


@pytest.fixture
def ebay_config():
    """Create a mock EbayConfig."""
    config = Mock(spec=EbayConfig)
    config.marketplace_id = "EBAY_US"
    config.location_key = "location123"
    config.listing_policies = Mock()
    config.listing_policies.fulfillment_policy_id = "fp123"
    config.listing_policies.payment_policy_id = "pp123"
    config.listing_policies.return_policy_id = "rp123"
    return config


@pytest.fixture
def mock_clients(mocker):
    """Create mock eBay client dependencies."""
    selling_client = mocker.create_autospec(EbaySellingClient, instance=True)
    taxonomy_client = mocker.create_autospec(EbayTaxonomyClient, instance=True)
    commerce_client = mocker.create_autospec(EbayCommerceClient, instance=True)
    
    return EbayClients(
        selling_client=selling_client,
        taxonomy_client=taxonomy_client,
        commerce_client=commerce_client,
    )


@pytest.fixture
def ebay_api(ebay_config, mock_clients):
    """Create EbayAPI instance with mocked dependencies."""
    return EbayAPI(ebay_config, mock_clients)


# -------------------- TEST: get_category_id -------------------- #

def test_get_category_id_success(ebay_api, mock_clients):
    """Test successful category ID lookup."""
    tree = ebay_models.CategoryTree(
        applicable_marketplace_ids=["EBAY_US"],
        category_tree_id="tree123",
        category_tree_version="v1",
        root_category_node=ebay_models.CategoryTreeNode(
            category=ebay_models.Category(category_id="cat1", category_name="Electronics"),
            category_tree_node_level=1,
            child_category_tree_nodes=[
                ebay_models.CategoryTreeNode(
                    category=ebay_models.Category(category_id="cat2", category_name="Phones"),
                    category_tree_node_level=2,
                    leaf_category_tree_node=True,
                    child_category_tree_nodes=[],
                )
            ],
            leaf_category_tree_node=False,
        ),
    )

    mock_clients.taxonomy_client.get_default_tree_id.return_value = "tree123"
    mock_clients.taxonomy_client.fetch_category_tree.return_value = tree

    cat_id, cat_name = ebay_api.get_category_id("Phones")

    assert cat_id == "cat2"
    assert cat_name == "Phones"
    mock_clients.taxonomy_client.get_default_tree_id.assert_called_once_with("EBAY_US")
    mock_clients.taxonomy_client.fetch_category_tree.assert_called_once_with("tree123")


def test_get_category_id_not_found(ebay_api, mock_clients):
    """Test category not found raises CategoryNotExistsError."""
    tree = ebay_models.CategoryTree(
        applicable_marketplace_ids=["EBAY_US"],
        category_tree_id="tree123",
        category_tree_version="v1",
        root_category_node=ebay_models.CategoryTreeNode(
            category=ebay_models.Category(category_id="cat1", category_name="Electronics"),
            category_tree_node_level=1,
            child_category_tree_nodes=[],
            leaf_category_tree_node=False,
        ),
    )

    mock_clients.taxonomy_client.get_default_tree_id.return_value = "tree123"
    mock_clients.taxonomy_client.fetch_category_tree.return_value = tree

    with pytest.raises(CategoryNotExistsError, match="not found"):
        ebay_api.get_category_id("NonExistent")


def test_get_category_id_taxonomy_client_error(ebay_api, mock_clients):
    """Test taxonomy client error is wrapped in MarketplaceAPIError."""
    mock_clients.taxonomy_client.get_default_tree_id.side_effect = EbayTaxonomyClientError()

    with pytest.raises(MarketplaceAPIError):
        ebay_api.get_category_id("Phones")


# -------------------- TEST: get_product_aspects -------------------- #

def test_get_product_aspects_success(ebay_api, mock_clients):
    """Test successful retrieval of product aspects."""
    tree = ebay_models.CategoryTree(
        applicable_marketplace_ids=["EBAY_US"],
        category_tree_id="tree123",
        category_tree_version="v1",
        root_category_node=ebay_models.CategoryTreeNode(
            category=ebay_models.Category(category_id="cat2", category_name="Phones"),
            category_tree_node_level=2,
            leaf_category_tree_node=True,
            child_category_tree_nodes=[],
        ),
    )

    aspect_metadata = ebay_models.AspectMetadata(
        aspects=[
            ebay_models.Aspect(
                localized_aspect_name="Brand",
                aspect_constraint=ebay_models.AspectConstraint(
                    aspect_data_type=ebay_models.AspectDataTypeEnum.STRING,
                    aspect_mode=ebay_models.AspectModeEnum.SELECTION_ONLY,
                    aspect_required=True,
                    aspect_usage=ebay_models.AspectUsageEnum.RECOMMENDED,
                    item_to_aspect_cardinality=ebay_models.ItemToAspectCardinalityEnum.SINGLE,
                    aspect_enabled_for_variations=False,
                ),
                aspect_values=[
                    ebay_models.AspectValue(localized_value="Apple"),
                    ebay_models.AspectValue(localized_value="Samsung"),
                ],
            )
        ]
    )

    mock_clients.taxonomy_client.get_default_tree_id.return_value = "tree123"
    mock_clients.taxonomy_client.fetch_category_tree.return_value = tree
    mock_clients.taxonomy_client.get_item_aspects.return_value = aspect_metadata

    aspects = ebay_api.get_product_aspects("Phones")

    assert len(aspects) == 1
    assert aspects[0].name == "Brand"
    assert aspects[0].data_type == AspectType.STR
    assert aspects[0].is_required is True
    assert aspects[0].allowed_values == frozenset(["Apple", "Samsung"])


def test_get_product_aspects_not_found(ebay_api, mock_clients):
    """Test category not found in get_product_aspects."""
    tree = ebay_models.CategoryTree(
        applicable_marketplace_ids=["EBAY_US"],
        category_tree_id="tree123",
        category_tree_version="v1",
        root_category_node=ebay_models.CategoryTreeNode(
            category=ebay_models.Category(category_id="cat1", category_name="Electronics"),
            category_tree_node_level=1,
            child_category_tree_nodes=[],
            leaf_category_tree_node=False,
        ),
    )

    mock_clients.taxonomy_client.get_default_tree_id.return_value = "tree123"
    mock_clients.taxonomy_client.fetch_category_tree.return_value = tree

    with pytest.raises(CategoryNotExistsError):
        ebay_api.get_product_aspects("NonExistent")


# -------------------- TEST: _search_category -------------------- #

def test_search_category_found_in_leaf(ebay_api):
    """Test category search finds category in leaf node."""
    tree = ebay_models.CategoryTree(
        applicable_marketplace_ids=["EBAY_US"],
        category_tree_id="tree123",
        category_tree_version="v1",
        root_category_node=ebay_models.CategoryTreeNode(
            category=ebay_models.Category(category_id="cat1", category_name="Electronics"),
            category_tree_node_level=1,
            child_category_tree_nodes=[
                ebay_models.CategoryTreeNode(
                    category=ebay_models.Category(category_id="cat2", category_name="Phones"),
                    category_tree_node_level=2,
                    leaf_category_tree_node=True,
                    child_category_tree_nodes=[],
                )
            ],
            leaf_category_tree_node=False,
        ),
    )

    result = ebay_api._search_category(tree, "Phones")
    assert result == ("cat2", "Phones")


def test_search_category_case_insensitive(ebay_api):
    """Test category search is case-insensitive."""
    tree = ebay_models.CategoryTree(
        applicable_marketplace_ids=["EBAY_US"],
        category_tree_id="tree123",
        category_tree_version="v1",
        root_category_node=ebay_models.CategoryTreeNode(
            category=ebay_models.Category(category_id="cat1", category_name="Electronics"),
            category_tree_node_level=1,
            child_category_tree_nodes=[],
            leaf_category_tree_node=True,
        ),
    )

    result = ebay_api._search_category(tree, "electronics")
    assert result == ("cat1", "Electronics")


def test_search_category_not_found(ebay_api):
    """Test category search returns None when not found."""
    tree = ebay_models.CategoryTree(
        applicable_marketplace_ids=["EBAY_US"],
        category_tree_id="tree123",
        category_tree_version="v1",
        root_category_node=ebay_models.CategoryTreeNode(
            category=ebay_models.Category(category_id="cat1", category_name="Electronics"),
            category_tree_node_level=1,
            child_category_tree_nodes=[],
            leaf_category_tree_node=True,
        ),
    )

    result = ebay_api._search_category(tree, "NonExistent")
    assert result is None


# -------------------- TEST: _from_ebay_aspects -------------------- #

def test_from_ebay_aspects_converts_correctly(ebay_api):
    """Test conversion from eBay aspects to domain aspects."""
    ebay_aspects = ebay_models.AspectMetadata(
        aspects=[
            ebay_models.Aspect(
                localized_aspect_name="Brand",
                aspect_constraint=ebay_models.AspectConstraint(
                    aspect_data_type=ebay_models.AspectDataTypeEnum.STRING,
                    aspect_mode=ebay_models.AspectModeEnum.SELECTION_ONLY,
                    aspect_required=False,
                    aspect_usage=ebay_models.AspectUsageEnum.OPTIONAL,
                    item_to_aspect_cardinality=ebay_models.ItemToAspectCardinalityEnum.SINGLE,
                    aspect_enabled_for_variations=False,
                ),
                aspect_values=[ebay_models.AspectValue(localized_value="Apple")],
            ),
            ebay_models.Aspect(
                localized_aspect_name="Quantity",
                aspect_constraint=ebay_models.AspectConstraint(
                    aspect_data_type=ebay_models.AspectDataTypeEnum.NUMBER,
                    aspect_mode=ebay_models.AspectModeEnum.FREE_TEXT,
                    aspect_required=True,
                    aspect_usage=ebay_models.AspectUsageEnum.RECOMMENDED,
                    item_to_aspect_cardinality=ebay_models.ItemToAspectCardinalityEnum.SINGLE,
                    aspect_enabled_for_variations=False,
                ),
                aspect_values=[],
            ),
            ebay_models.Aspect(
                localized_aspect_name="Colors",
                aspect_constraint=ebay_models.AspectConstraint(
                    aspect_data_type=ebay_models.AspectDataTypeEnum.STRING_ARRAY,
                    aspect_mode=ebay_models.AspectModeEnum.SELECTION_ONLY,
                    aspect_required=False,
                    aspect_usage=ebay_models.AspectUsageEnum.OPTIONAL,
                    item_to_aspect_cardinality=ebay_models.ItemToAspectCardinalityEnum.MULTI,
                    aspect_enabled_for_variations=False,
                ),
                aspect_values=[],
            ),
        ]
    )

    aspects = ebay_api._from_ebay_aspects(ebay_aspects)

    assert len(aspects) == 3
    assert aspects[0].name == "Brand"
    assert aspects[0].data_type == AspectType.STR
    assert aspects[0].is_required is False
    
    assert aspects[1].name == "Quantity"
    assert aspects[1].data_type == AspectType.FLOAT
    assert aspects[1].is_required is True
    
    assert aspects[2].name == "Colors"
    assert aspects[2].data_type == AspectType.LIST


# -------------------- TEST: _product_to_inventory_item -------------------- #

def test_product_to_inventory_item_success(ebay_api):
    """Test successful conversion of item to inventory item."""
    aspect = AspectData(name="Brand", value="Apple", is_required=False)
    item = Mock(spec=EbayItem)
    item.product = Mock()
    item.product.aspects = [aspect]
    item.title = "iPhone 13"
    item.description = "Latest iPhone model"
    item.quantity = 5
    
    marketplace_aspects = EbayMarketplaceAspects(
        marketplace="EBAY_US",
        package=Package(
            weight=Weight(unit="POUND", value=0.5),
            dimensions=Dimension(height=1.0, length=1.0, width=1.0, unit="INCH"),
        ),
        condition="NEW",
        condition_description="Brand new",
    )
    item.marketplace_aspects = marketplace_aspects
    
    images_urls = ["https://img.ebay.com/img1.jpg"]
    
    inventory_item = ebay_api._product_to_inventory_item(item, images_urls)
    
    assert inventory_item.product.title == "iPhone 13"
    assert inventory_item.product.description == "Latest iPhone model"
    assert inventory_item.product.aspects == {"Brand": ["Apple"]}
    assert inventory_item.product.image_urls == images_urls
    assert inventory_item.condition == "NEW"
    assert inventory_item.condition_description == "Brand new"
    assert inventory_item.availability.ship_to_location_availability.quantity == 5



# -------------------- TEST: _get_listing_policies -------------------- #

def test_get_listing_policies(ebay_api, ebay_config):
    """Test listing policies conversion."""
    policies = ebay_api._get_listing_policies()
    
    assert policies.fulfillment_policy_id == "fp123"
    assert policies.payment_policy_id == "pp123"
    assert policies.return_policy_id == "rp123"


# -------------------- TEST: _make_offer -------------------- #

def test_make_offer(ebay_api):
    """Test offer creation."""
    offer = ebay_api._make_offer("SKU123", "cat123", "USD", 99.99)
    
    assert offer.sku == "SKU123"
    assert offer.category_id == "cat123"
    assert offer.format == "FIXED_PRICE"
    assert offer.marketplace_id == "EBAY_US"
    # Check for either field name (location_key or merchant_location_key)
    location_key = getattr(offer, "merchant_location_key", None) or getattr(offer, "location_key", None)
    assert location_key == "location123"
    assert offer.pricing_summary.price.currency == "USD"
    assert offer.pricing_summary.price.value == 99.99


# -------------------- TEST: publish -------------------- #

def test_publish_success(ebay_api, mock_clients):
    """Test successful item publishing."""
    tree = ebay_models.CategoryTree(
        applicable_marketplace_ids=["EBAY_US"],
        category_tree_id="tree123",
        category_tree_version="v1",
        root_category_node=ebay_models.CategoryTreeNode(
            category=ebay_models.Category(category_id="cat2", category_name="Phones"),
            category_tree_node_level=2,
            leaf_category_tree_node=True,
            child_category_tree_nodes=[],
        ),
    )

    aspect = AspectData(name="Brand", value="Apple", is_required=False)
    item = Mock(spec=EbayItem)
    item.product = Mock()
    item.product.aspects = [aspect]
    item.title = "iPhone"
    item.description = "Test"
    item.quantity = 1
    item.category = "Phones"
    item.currency = "USD"
    item.price = 99.99
    
    marketplace_aspects = EbayMarketplaceAspects(
        marketplace="EBAY_US",
        package=Package(weight=Weight(unit="POUND", value=0.5)),
        condition="NEW",
    )
    item.marketplace_aspects = marketplace_aspects

    mock_clients.taxonomy_client.get_default_tree_id.return_value = "tree123"
    mock_clients.taxonomy_client.fetch_category_tree.return_value = tree
    
    img_response = Mock()
    img_response.image_url = "https://img.ebay.com/img.jpg"
    mock_clients.commerce_client.upload_image.return_value = img_response
    
    mock_clients.selling_client.create_offer.return_value = "offer123"

    ebay_api.publish(item, "img.jpg")

    mock_clients.commerce_client.upload_image.assert_called_once_with("img.jpg")
    mock_clients.selling_client.create_or_replace_inventory_item.assert_called_once()
    mock_clients.selling_client.create_offer.assert_called_once()
    mock_clients.selling_client.publish_offer.assert_called_once_with("offer123")


def test_publish_commerce_error(ebay_api, mock_clients):
    """Test publish handles commerce client error."""
    tree = ebay_models.CategoryTree(
        applicable_marketplace_ids=["EBAY_US"],
        category_tree_id="tree123",
        category_tree_version="v1",
        root_category_node=ebay_models.CategoryTreeNode(
            category=ebay_models.Category(category_id="cat2", category_name="Phones"),
            category_tree_node_level=2,
            leaf_category_tree_node=True,
            child_category_tree_nodes=[],
        ),
    )

    item = Mock(spec=EbayItem)
    item.product = Mock()
    item.product.aspects = []
    item.title = "iPhone"
    item.description = "Test"
    item.quantity = 1
    item.category = "Phones"
    
    marketplace_aspects = EbayMarketplaceAspects(
        marketplace="EBAY_US",
        package=Package(weight=Weight(unit="POUND", value=0.5)),
        condition="NEW",
    )
    item.marketplace_aspects = marketplace_aspects

    mock_clients.taxonomy_client.get_default_tree_id.return_value = "tree123"
    mock_clients.taxonomy_client.fetch_category_tree.return_value = tree
    mock_clients.commerce_client.upload_image.side_effect = CommerceClientError()

    with pytest.raises(MarketplaceAPIError):
        ebay_api.publish(item, "img.jpg")
