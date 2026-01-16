"""Tests for services.search module."""

import pytest
from unittest.mock import Mock, AsyncMock, MagicMock

from app.services.search import SearchService
from app.domain.dto import ProductCategoriesDTO, ProductDTO
from app.domain.entities import ProductStructure, AspectField, AspectType, Product
from app.domain.ports import (
    ProductCategoriesNotFound,
    SearchServiceError,
)
from app.services.ports import (
    CategoriesNotFoundError,
    ICategoryPredictorFactory,
    IMarketplaceAPIFactory,
    ISearchEngine,
    SearchEngineError,
)


@pytest.fixture
def mock_search_engine():
    """Create a mock search engine."""
    engine = Mock(spec=ISearchEngine)
    return engine


@pytest.fixture
def mock_api_factory():
    """Create a mock marketplace API factory."""
    factory = Mock(spec=IMarketplaceAPIFactory)
    return factory


@pytest.fixture
def mock_predictors_factory():
    """Create a mock category predictor factory."""
    factory = Mock(spec=ICategoryPredictorFactory)
    return factory


@pytest.fixture
def search_service(mock_search_engine, mock_api_factory, mock_predictors_factory):
    """Create SearchService with mocked dependencies."""
    return SearchService(
        search=mock_search_engine,
        api_factory=mock_api_factory,
        predictors_factory=mock_predictors_factory,
    )


@pytest.fixture
def mock_product():
    """Create a mock product."""
    product = Mock(spec=Product)
    product.metadata = Mock()
    product.metadata.asdict.return_value = {"title": "Test", "description": "Test"}
    product.aspects = []
    return product


@pytest.fixture
def mock_marketplace_api():
    """Create a mock marketplace API."""
    api = Mock()
    api.get_product_aspects.return_value = [
        AspectField(name="brand", data_type=AspectType.STR, is_required=True),
        AspectField(name="color", data_type=AspectType.STR, is_required=False),
    ]
    return api


class TestSearchServiceProductAspects:
    """Tests for SearchService.product_aspects method."""

    def test_product_aspects_success(
        self,
        search_service,
        mock_api_factory,
        mock_search_engine,
        mock_marketplace_api,
        mock_product,
    ):
        """Test successful product aspects retrieval."""
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_search_engine.by_product_name.return_value = mock_product

        result = search_service.product_aspects(
            product_name="iPhone 13",
            category="Phones",
            comment="Latest model",
            marketplace="EBAY_US",
        )

        assert isinstance(result, ProductDTO)
        mock_api_factory.get.assert_called_once_with("EBAY_US")
        mock_marketplace_api.get_product_aspects.assert_called_once_with("Phones")

    def test_product_aspects_with_settings(
        self,
        search_service,
        mock_api_factory,
        mock_search_engine,
        mock_marketplace_api,
        mock_product,
    ):
        """Test product aspects with additional settings."""
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_search_engine.by_product_name.return_value = mock_product

        settings = {"region": "US", "language": "en"}
        result = search_service.product_aspects(
            product_name="Samsung Galaxy",
            category="Phones",
            comment="",
            marketplace="EBAY_UK",
            **settings,
        )

        assert isinstance(result, ProductDTO)
        mock_marketplace_api.get_product_aspects.assert_called_once_with(
            "Phones", **settings
        )

    def test_product_aspects_search_engine_error(
        self,
        search_service,
        mock_api_factory,
        mock_search_engine,
        mock_marketplace_api,
    ):
        """Test that SearchEngineError is wrapped in SearchServiceError."""
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_search_engine.by_product_name.side_effect = SearchEngineError(
            "Search failed"
        )

        with pytest.raises(SearchServiceError):
            search_service.product_aspects(
                product_name="Test",
                category="Category",
                comment="",
                marketplace="EBAY_US",
            )

    def test_product_aspects_no_aspects_found(
        self,
        search_service,
        mock_api_factory,
        mock_marketplace_api,
        mock_search_engine,
        mock_product,
    ):
        """Test when no aspects are found for category."""
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_marketplace_api.get_product_aspects.return_value = ProductStructure(
            fields=[]
        )
        mock_search_engine.by_product_name.return_value = mock_product

        result = search_service.product_aspects(
            product_name="Unknown",
            category="UnknownCategory",
            comment="",
            marketplace="EBAY_US",
        )

        # Should still work with empty aspects
        assert result is not None

    def test_product_aspects_with_empty_comment(
        self,
        search_service,
        mock_api_factory,
        mock_search_engine,
        mock_marketplace_api,
        mock_product,
    ):
        """Test product aspects with empty comment."""
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_search_engine.by_product_name.return_value = mock_product

        result = search_service.product_aspects(
            product_name="Product",
            category="Category",
            comment="",
            marketplace="EBAY_US",
        )

        assert isinstance(result, ProductDTO)


class TestSearchServiceRecognizeProduct:
    """Tests for SearchService.recognize_product method."""

    def test_recognize_product_success(
        self,
        search_service,
        mock_search_engine,
        mock_predictors_factory,
    ):
        """Test successful product recognition from image."""
        mock_search_engine.barecodes_on_image.return_value = ["123456789"]
        mock_search_engine.product_name_by_barecode.return_value = "iPhone 13"

        mock_predictor = Mock()
        mock_predictor.predict.return_value = ["Phones", "Electronics"]
        mock_predictors_factory.get.return_value = mock_predictor

        result = search_service.recognize_product(
            img_path="/path/to/image.jpg",
            marketplace="EBAY_US",
        )

        assert isinstance(result, ProductCategoriesDTO)
        assert result.product_name == "iPhone 13"
        assert "Phones" in result.categories

    def test_recognize_product_with_settings(
        self,
        search_service,
        mock_search_engine,
        mock_predictors_factory,
    ):
        """Test product recognition with additional settings."""
        mock_search_engine.barecodes_on_image.return_value = ["987654321"]
        mock_search_engine.product_name_by_barecode.return_value = "Samsung Galaxy"

        mock_predictor = Mock()
        mock_predictor.predict.return_value = ["Phones"]
        mock_predictors_factory.get.return_value = mock_predictor

        settings = {"confidence": 0.9}
        result = search_service.recognize_product(
            img_path="/path/to/image.jpg", marketplace="EBAY_UK", **settings
        )

        assert isinstance(result, ProductCategoriesDTO)
        mock_predictor.predict.assert_called_once_with("Samsung Galaxy", **settings)

    def test_recognize_product_no_barcode_raises_error(
        self, search_service, mock_search_engine
    ):
        """Test that image without barcode raises SearchServiceError."""
        mock_search_engine.barecodes_on_image.return_value = []

        with pytest.raises(SearchServiceError, match="exactly one barcode"):
            search_service.recognize_product(
                img_path="/path/to/image.jpg",
                marketplace="EBAY_US",
            )

    def test_recognize_product_multiple_barcodes_raises_error(
        self, search_service, mock_search_engine
    ):
        """Test that image with multiple barcodes raises SearchServiceError."""
        mock_search_engine.barecodes_on_image.return_value = ["barcode1", "barcode2"]

        with pytest.raises(SearchServiceError, match="exactly one barcode"):
            search_service.recognize_product(
                img_path="/path/to/image.jpg",
                marketplace="EBAY_US",
            )

    def test_recognize_product_category_not_found(
        self,
        search_service,
        mock_search_engine,
        mock_predictors_factory,
    ):
        """Test that CategoriesNotFoundError is wrapped in ProductCategoriesNotFound."""
        mock_search_engine.barecodes_on_image.return_value = ["123456789"]
        mock_search_engine.product_name_by_barecode.return_value = "Unknown Product"

        mock_predictor = Mock()
        mock_predictor.predict.side_effect = CategoriesNotFoundError("Not found")
        mock_predictors_factory.get.return_value = mock_predictor

        with pytest.raises(ProductCategoriesNotFound):
            search_service.recognize_product(
                img_path="/path/to/image.jpg",
                marketplace="EBAY_US",
            )

    def test_recognize_product_search_engine_error(
        self,
        search_service,
        mock_search_engine,
    ):
        """Test that SearchEngineError during image processing is not wrapped (outside try-except)."""
        mock_search_engine.barecodes_on_image.side_effect = SearchEngineError(
            "Image processing failed"
        )

        # SearchEngineError from barecodes_on_image is not wrapped (called before try-except)
        with pytest.raises(SearchEngineError):
            search_service.recognize_product(
                img_path="/path/to/image.jpg",
                marketplace="EBAY_US",
            )

    def test_recognize_product_barcode_lookup_error(
        self,
        search_service,
        mock_search_engine,
    ):
        """Test that SearchEngineError during barcode lookup is wrapped."""
        mock_search_engine.barecodes_on_image.return_value = ["123456789"]
        mock_search_engine.product_name_by_barecode.side_effect = SearchEngineError(
            "Lookup failed"
        )

        with pytest.raises(SearchServiceError):
            search_service.recognize_product(
                img_path="/path/to/image.jpg",
                marketplace="EBAY_US",
            )


class TestSearchServiceFactoryUsage:
    """Tests for SearchService factory usage."""

    def test_api_factory_called_with_marketplace(
        self,
        search_service,
        mock_api_factory,
        mock_search_engine,
        mock_marketplace_api,
        mock_product,
    ):
        """Test that API factory is called with correct marketplace."""
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_search_engine.by_product_name.return_value = mock_product

        search_service.product_aspects(
            product_name="Test",
            category="Category",
            comment="",
            marketplace="EBAY_DE",
        )

        mock_api_factory.get.assert_called_once_with("EBAY_DE")

    def test_predictor_factory_called_with_marketplace(
        self,
        search_service,
        mock_search_engine,
        mock_predictors_factory,
    ):
        """Test that predictor factory is called with correct marketplace."""
        mock_search_engine.barecodes_on_image.return_value = ["123456789"]
        mock_search_engine.product_name_by_barecode.return_value = "Product"

        mock_predictor = Mock()
        mock_predictor.predict.return_value = ["Category"]
        mock_predictors_factory.get.return_value = mock_predictor

        search_service.recognize_product(
            img_path="/path/to/image.jpg",
            marketplace="EBAY_FR",
        )

        mock_predictors_factory.get.assert_called_once_with("EBAY_FR")


class TestSearchServiceIntegration:
    """Integration tests for SearchService."""

    def test_product_aspects_creates_product_structure(
        self,
        search_service,
        mock_api_factory,
        mock_search_engine,
        mock_marketplace_api,
        mock_product,
    ):
        """Test that product structure is created with aspects from API."""
        aspects = [
            AspectField(name="brand", data_type=AspectType.STR, is_required=True),
            AspectField(name="color", data_type=AspectType.STR, is_required=False),
        ]
        mock_marketplace_api.get_product_aspects.return_value = aspects
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_search_engine.by_product_name.return_value = mock_product

        result = search_service.product_aspects(
            product_name="Test Product",
            category="Category",
            comment="Test comment",
            marketplace="EBAY_US",
        )

        assert isinstance(result, ProductDTO)
        mock_search_engine.by_product_name.assert_called_once()

    def test_recognize_product_complete_workflow(
        self,
        search_service,
        mock_search_engine,
        mock_predictors_factory,
    ):
        """Test complete product recognition workflow."""
        barcode = "EAN123456789"
        product_name = "Sony Headphones"
        categories = ["Electronics", "Audio Equipment"]

        mock_search_engine.barecodes_on_image.return_value = [barcode]
        mock_search_engine.product_name_by_barecode.return_value = product_name

        mock_predictor = Mock()
        mock_predictor.predict.return_value = categories
        mock_predictors_factory.get.return_value = mock_predictor

        result = search_service.recognize_product(
            img_path="/path/to/image.jpg",
            marketplace="EBAY_US",
        )

        assert result.product_name == product_name
        assert categories == result.categories
