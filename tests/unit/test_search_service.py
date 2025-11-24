import pytest

from app.core.domain.question import Answer
from app.core.infrastructure.adapter import (
    InvalidMetadata,
    InvalidProduct,
    QuestionAdapterABC,
)
from app.core.infrastructure.marketplace import MarketplaceAPI
from app.core.infrastructure.search import (
    CategoriesNotFoundError,
    SearchEngine,
    SearchEngineError,
)
from app.core.services.search import (
    ProductCategories,
    ProductCategoriesNotFoundError,
    SearchError,
    SearchService,
)


@pytest.fixture
def service_with_mocks(mocker):
    """Fixture that sets up SearchService with all dependencies mocked via pytest-mock."""
    search = mocker.create_autospec(SearchEngine, instance=True)
    marketplace_api = mocker.create_autospec(MarketplaceAPI, instance=True)
    adapter = mocker.create_autospec(QuestionAdapterABC, instance=True)
    metadata_type = mocker.Mock(name="MetadataType")

    service = SearchService(search, marketplace_api, adapter, metadata_type)
    return service, search, marketplace_api, adapter


# -------------------- TEST: product() -------------------- #


def test_product_success(service_with_mocks):
    service, search, marketplace_api, adapter = service_with_mocks

    marketplace_api.get_product_aspects.return_value = ["aspect1"]
    adapter.to_schema.return_value = {"type": "object"}
    search.by_product_name.return_value = {"foo": "bar"}

    expected_answer = Answer(metadata="meta", product_data="data")
    adapter.to_answer.return_value = expected_answer

    result = service.product("Phone", "Electronics", "Nice model")

    marketplace_api.get_product_aspects.assert_called_once_with("Electronics")
    adapter.to_schema.assert_called_once()
    search.by_product_name.assert_called_once_with(
        "Phone", "Nice model", {"type": "object"}
    )
    adapter.to_answer.assert_called_once()
    assert result == expected_answer


def test_product_search_engine_error(service_with_mocks):
    service, search, marketplace_api, adapter = service_with_mocks

    marketplace_api.get_product_aspects.return_value = ["aspect"]
    adapter.to_schema.return_value = {"schema": True}
    search.by_product_name.side_effect = SearchEngineError()

    with pytest.raises(SearchError):
        service.product("Phone", "Electronics", "")


def test_product_invalid_product_error(service_with_mocks):
    service, search, marketplace_api, adapter = service_with_mocks

    marketplace_api.get_product_aspects.return_value = ["aspect"]
    adapter.to_schema.return_value = {"schema": True}
    search.by_product_name.return_value = {"raw": True}
    adapter.to_answer.side_effect = InvalidProduct()

    with pytest.raises(SearchError, match="Failed to parse product aspects data"):
        service.product("Phone", "Electronics", "")


def test_product_invalid_metadata_error(service_with_mocks):
    service, search, marketplace_api, adapter = service_with_mocks

    marketplace_api.get_product_aspects.return_value = ["aspect"]
    adapter.to_schema.return_value = {"schema": True}
    search.by_product_name.return_value = {"raw": True}
    adapter.to_answer.side_effect = InvalidMetadata()

    with pytest.raises(SearchError, match="Failed to parse product metadata"):
        service.product("Phone", "Electronics", "")


# -------------------- TEST: product_categories() -------------------- #


def test_product_categories_success(service_with_mocks):
    service, search, _, _ = service_with_mocks

    search.barecodes_on_image.return_value = ["12345"]
    search.by_barecode.return_value = "iPhone 13"
    search.categories.return_value = ["Phones", "Electronics"]

    result = service.product_categories("test.jpg")

    search.barecodes_on_image.assert_called_once_with("test.jpg")
    search.by_barecode.assert_called_once_with("12345")
    search.categories.assert_called_once_with("iPhone 13")

    assert isinstance(result, ProductCategories)
    assert result.product_name == "iPhone 13"
    assert result.categories == ["Phones", "Electronics"]


@pytest.mark.parametrize("barcodes", [[], ["1", "2"]])
def test_product_categories_invalid_barcode_count(service_with_mocks, barcodes):
    service, search, _, _ = service_with_mocks
    search.barecodes_on_image.return_value = barcodes

    with pytest.raises(SearchError, match="Image must contain exactly one barcode"):
        service.product_categories("img.png")


def test_product_categories_not_found(service_with_mocks):
    service, search, _, _ = service_with_mocks

    search.barecodes_on_image.return_value = ["999"]
    search.by_barecode.return_value = "ProductX"
    search.categories.side_effect = CategoriesNotFoundError()

    with pytest.raises(ProductCategoriesNotFoundError):
        service.product_categories("img.jpg")


def test_product_categories_search_engine_error_on_barecode(service_with_mocks):
    service, search, _, _ = service_with_mocks

    search.barecodes_on_image.return_value = ["999"]
    search.by_barecode.side_effect = SearchEngineError()

    with pytest.raises(SearchError):
        service.product_categories("img.jpg")


def test_product_categories_search_engine_error_on_categories(service_with_mocks):
    service, search, _, _ = service_with_mocks

    search.barecodes_on_image.return_value = ["999"]
    search.by_barecode.return_value = "Product"
    search.categories.side_effect = SearchEngineError()

    with pytest.raises(SearchError):
        service.product_categories("img.jpg")
