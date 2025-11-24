import pytest
from unittest.mock import Mock
from pydantic import BaseModel, ValidationError

from app.core.services.selling import (
    SellingService,
    SellingServiceABC,
    SellingError,
    CategoryNotFound,
    ItemData,
)
from app.core.infrastructure.marketplace import (
    MarketplaceAPI,
    MarketplaceAPIError,
    CategoryNotExistsError,
)
from app.core.domain.item import Product
from app.core.domain.value_objects import AspectField, AspectType


class FakeMarketplaceAspects(BaseModel):
    """Mock marketplace aspects for testing."""

    marketplace: str
    condition: str


@pytest.fixture
def mock_marketplace_api(mocker):
    """Create mock MarketplaceAPI."""
    api = mocker.create_autospec(MarketplaceAPI, instance=True)
    return api


@pytest.fixture
def selling_service(mock_marketplace_api):
    """Create SellingService with mocked marketplace API."""
    return SellingService(mock_marketplace_api, FakeMarketplaceAspects)


@pytest.fixture
def item_data():
    """Create valid ItemData for testing."""
    return ItemData(
        title="iPhone 13",
        description="Latest iPhone model",
        price=999.99,
        currency="USD",
        country="US",
        quantity=5,
        category="Phones",
    )


@pytest.fixture
def valid_product_aspects():
    """Create valid product aspect fields."""
    return [
        AspectField(
            name="brand",
            data_type=AspectType.STR,
            is_required=True,
            allowed_values=frozenset(["Apple", "Samsung"]),
        ),
        AspectField(
            name="storage",
            data_type=AspectType.STR,
            is_required=False,
            allowed_values=frozenset(["64GB", "128GB", "256GB"]),
        ),
    ]


@pytest.fixture
def valid_marketplace_aspects_data():
    """Create valid marketplace aspects data."""
    return {
        "marketplace": "EBAY_US",
        "condition": "NEW",
    }


@pytest.fixture
def valid_product_data():
    """Create valid product data."""
    return {
        "brand": "Apple",
        "storage": "128GB",
    }


# -------------------- TEST: sell_item -------------------- #


def test_sell_item_success(
    selling_service,
    mock_marketplace_api,
    item_data,
    valid_marketplace_aspects_data,
    valid_product_data,
    valid_product_aspects,
):
    """Test successful item selling."""
    mock_marketplace_api.get_product_aspects.return_value = valid_product_aspects

    selling_service.sell_item(
        item_data,
        valid_marketplace_aspects_data,
        valid_product_data,
        "image1.jpg",
        "image2.jpg",
    )

    mock_marketplace_api.get_product_aspects.assert_called_once_with("Phones")
    mock_marketplace_api.publish.assert_called_once()

    # Verify that publish was called with correct item and images
    call_args = mock_marketplace_api.publish.call_args
    published_item = call_args[0][0]
    images = call_args[0][1:]

    assert published_item.title == "iPhone 13"
    assert published_item.description == "Latest iPhone model"
    assert published_item.price == 999.99
    assert published_item.currency == "USD"
    assert published_item.quantity == 5
    assert published_item.category == "Phones"
    assert images == ("image1.jpg", "image2.jpg")


def test_sell_item_marketplace_api_error_on_publish(
    selling_service,
    mock_marketplace_api,
    item_data,
    valid_marketplace_aspects_data,
    valid_product_data,
    valid_product_aspects,
):
    """Test MarketplaceAPIError during publish raises SellingError."""
    mock_marketplace_api.get_product_aspects.return_value = valid_product_aspects
    mock_marketplace_api.publish.side_effect = MarketplaceAPIError()

    with pytest.raises(SellingError):
        selling_service.sell_item(
            item_data,
            valid_marketplace_aspects_data,
            valid_product_data,
            "image.jpg",
        )


def test_sell_item_invalid_marketplace_aspects(
    selling_service,
    mock_marketplace_api,
    item_data,
    valid_product_data,
    valid_product_aspects,
):
    """Test invalid marketplace aspects data raises error."""
    mock_marketplace_api.get_product_aspects.return_value = valid_product_aspects

    invalid_aspects = {"marketplace": "EBAY_US"}  # missing required condition field

    with pytest.raises(ValidationError):
        selling_service.sell_item(
            item_data,
            invalid_aspects,
            valid_product_data,
            "image.jpg",
        )


# -------------------- TEST: _validate_product_structure -------------------- #


def test_validate_product_structure_success(
    selling_service,
    mock_marketplace_api,
    valid_product_aspects,
    valid_product_data,
):
    """Test successful product structure validation."""
    mock_marketplace_api.get_product_aspects.return_value = valid_product_aspects

    product = selling_service._validate_product_structure("Phones", valid_product_data)

    assert isinstance(product, Product)
    assert len(product.aspects) == 2
    assert product.aspects[0].name == "brand"
    assert product.aspects[0].value == "Apple"
    assert product.aspects[1].name == "storage"
    assert product.aspects[1].value == "128GB"


def test_validate_product_structure_category_not_exists(
    selling_service,
    mock_marketplace_api,
):
    """Test CategoryNotExistsError is converted to CategoryNotFound."""
    mock_marketplace_api.get_product_aspects.side_effect = CategoryNotExistsError()

    with pytest.raises(CategoryNotFound):
        selling_service._validate_product_structure("NonExistent", {})


def test_validate_product_structure_marketplace_api_error(
    selling_service,
    mock_marketplace_api,
):
    """Test MarketplaceAPIError is converted to SellingError."""
    mock_marketplace_api.get_product_aspects.side_effect = MarketplaceAPIError()

    with pytest.raises(SellingError):
        selling_service._validate_product_structure("Phones", {})


def test_validate_product_structure_missing_required_aspect(
    selling_service,
    mock_marketplace_api,
    valid_product_aspects,
):
    """Test missing required aspect raises CategoryNotFound."""
    mock_marketplace_api.get_product_aspects.return_value = valid_product_aspects

    # Missing required 'brand' field
    product_data = {"storage": "128GB"}

    with pytest.raises(CategoryNotFound):
        selling_service._validate_product_structure("Phones", product_data)


def test_validate_product_structure_invalid_aspect_value(
    selling_service,
    mock_marketplace_api,
    valid_product_aspects,
):
    """Test invalid aspect value raises CategoryNotFound."""
    mock_marketplace_api.get_product_aspects.return_value = valid_product_aspects

    # Invalid brand value (not in allowed values)
    product_data = {"brand": "Sony", "storage": "128GB"}

    with pytest.raises(CategoryNotFound):
        selling_service._validate_product_structure("Phones", product_data)


def test_validate_product_structure_unexpected_aspect(
    selling_service,
    mock_marketplace_api,
    valid_product_aspects,
):
    """Test unexpected aspect in product data raises CategoryNotFound."""
    mock_marketplace_api.get_product_aspects.return_value = valid_product_aspects

    # Extra unexpected field
    product_data = {"brand": "Apple", "storage": "128GB", "extra": "field"}

    with pytest.raises(CategoryNotFound):
        selling_service._validate_product_structure("Phones", product_data)


def test_validate_product_structure_incorrect_type(
    selling_service,
    mock_marketplace_api,
    valid_product_aspects,
):
    """Test incorrect aspect type raises CategoryNotFound."""
    mock_marketplace_api.get_product_aspects.return_value = valid_product_aspects

    # Wrong type for brand (should be string)
    product_data = {"brand": 123, "storage": "128GB"}

    with pytest.raises(CategoryNotFound):
        selling_service._validate_product_structure("Phones", product_data)


# -------------------- TEST: sell_item with different aspect types -------------------- #


def test_sell_item_with_numeric_aspect(
    selling_service,
    mock_marketplace_api,
    item_data,
    valid_marketplace_aspects_data,
):
    """Test selling item with numeric aspect."""
    aspects = [
        AspectField(
            name="warranty_months",
            data_type=AspectType.INT,
            is_required=False,
        ),
    ]
    mock_marketplace_api.get_product_aspects.return_value = aspects

    product_data = {"warranty_months": 12}

    selling_service.sell_item(
        item_data,
        valid_marketplace_aspects_data,
        product_data,
        "image.jpg",
    )

    mock_marketplace_api.publish.assert_called_once()


def test_sell_item_with_list_aspect(
    selling_service,
    mock_marketplace_api,
    item_data,
    valid_marketplace_aspects_data,
):
    """Test selling item with list aspect."""
    aspects = [
        AspectField(
            name="colors",
            data_type=AspectType.LIST,
            is_required=False,
        ),
    ]
    mock_marketplace_api.get_product_aspects.return_value = aspects

    product_data = {"colors": ["red", "blue"]}

    selling_service.sell_item(
        item_data,
        valid_marketplace_aspects_data,
        product_data,
        "image.jpg",
    )

    mock_marketplace_api.publish.assert_called_once()


# -------------------- TEST: sell_item with multiple images -------------------- #


def test_sell_item_with_no_images(
    selling_service,
    mock_marketplace_api,
    item_data,
    valid_marketplace_aspects_data,
    valid_product_data,
    valid_product_aspects,
):
    """Test selling item with no images."""
    mock_marketplace_api.get_product_aspects.return_value = valid_product_aspects

    selling_service.sell_item(
        item_data,
        valid_marketplace_aspects_data,
        valid_product_data,
    )

    mock_marketplace_api.publish.assert_called_once()
    call_args = mock_marketplace_api.publish.call_args
    images = call_args[0][1:]
    assert images == ()


def test_sell_item_with_single_image(
    selling_service,
    mock_marketplace_api,
    item_data,
    valid_marketplace_aspects_data,
    valid_product_data,
    valid_product_aspects,
):
    """Test selling item with single image."""
    mock_marketplace_api.get_product_aspects.return_value = valid_product_aspects

    selling_service.sell_item(
        item_data,
        valid_marketplace_aspects_data,
        valid_product_data,
        "image.jpg",
    )

    call_args = mock_marketplace_api.publish.call_args
    images = call_args[0][1:]
    assert images == ("image.jpg",)


# -------------------- TEST: SellingServiceABC interface -------------------- #


def test_selling_service_implements_interface():
    """Test that SellingService implements SellingServiceABC."""
    assert isinstance(
        SellingService(Mock(spec=MarketplaceAPI), FakeMarketplaceAspects),
        SellingServiceABC,
    )


def test_selling_service_has_sell_item_method():
    """Test that SellingService has sell_item method."""
    service = SellingService(Mock(spec=MarketplaceAPI), FakeMarketplaceAspects)
    assert hasattr(service, "sell_item")
    assert callable(service.sell_item)
