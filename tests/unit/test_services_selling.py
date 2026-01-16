"""Tests for services.selling module."""

import pytest
from unittest.mock import Mock, AsyncMock

from app.domain.ports.errors import InvalidCategory
from app.services.selling import SellingService
from app.domain.dto import ItemDTO, MarketplaceAccountDTO
from app.domain.entities import AspectField, AspectType
from app.domain.ports import SellingServiceError
from app.services.ports import (
    CategoryNotFound,
    IAccessTokenStorage,
    IMarketplaceAPIFactory,
    IMarketplaceAspectsFactory,
    IMarketplaceOAuthFactory,
    IRefreshTokenStorage,
    MarketplaceAPIError,
    AuthToken,
)


class MockMarketplaceAspects:
    """Mock marketplace aspects for testing."""

    @staticmethod
    def validate(data):
        return Mock(
            marketplace="mockmarket",
            policies=Mock(
                fulfillment_policy_id="fp123",
                payment_policy_id="pp123",
                return_policy_id="rp123",
            ),
        )


@pytest.fixture
def mock_api_factory():
    """Create a mock marketplace API factory."""
    factory = Mock(spec=IMarketplaceAPIFactory)
    return factory


@pytest.fixture
def mock_access_token_storage():
    """Create a mock access token storage."""
    storage = AsyncMock(spec=IAccessTokenStorage)
    return storage


@pytest.fixture
def mock_refresh_token_storage():
    """Create a mock refresh token storage."""
    storage = AsyncMock(spec=IRefreshTokenStorage)
    return storage


@pytest.fixture
def mock_oauth_factory():
    """Create a mock OAuth factory."""
    factory = Mock(spec=IMarketplaceOAuthFactory)
    return factory


@pytest.fixture
def mock_aspects_factory():
    """Create a mock marketplace aspects factory."""
    factory = Mock(spec=IMarketplaceAspectsFactory)
    factory.get.return_value = MockMarketplaceAspects
    return factory


@pytest.fixture
def selling_service(
    mock_api_factory,
    mock_access_token_storage,
    mock_refresh_token_storage,
    mock_oauth_factory,
    mock_aspects_factory,
):
    """Create SellingService with mocked dependencies."""
    return SellingService(
        api_factory=mock_api_factory,
        access_token_storage=mock_access_token_storage,
        refresh_token_storage=mock_refresh_token_storage,
        oauth_factory=mock_oauth_factory,
        token_ttl_threshold=300,
        type_factory=mock_aspects_factory,
    )


@pytest.fixture
def sample_item_dto():
    """Create a sample ItemDTO for testing."""
    return ItemDTO(
        title="Test Product",
        description="Test Description",
        price=99.99,
        currency="USD",
        country="US",
        category="Electronics",
        product_aspects={
            "brand": "Apple",
            "model": "iPhone 13",
        },
        marketplace_aspects_data={
            "marketplace": "mockmarket",
        },
        quantity=5,
    )


@pytest.fixture
def sample_account_dto():
    """Create a sample MarketplaceAccountDTO for testing."""
    return MarketplaceAccountDTO(
        user_uuid="550e8400-e29b-41d4-a716-446655440000",
        marketplace="mockmarket",
    )


@pytest.fixture
def mock_marketplace_api():
    """Create a mock marketplace API."""
    api = Mock()
    api.get_product_aspects.return_value = [
        AspectField(name="brand", data_type=AspectType.STR, is_required=True),
    ]

    return api


class TestSellingServicePublish:
    """Tests for SellingService.publish method."""

    @pytest.mark.asyncio
    async def test_publish_success(
        self,
        selling_service,
        mock_api_factory,
        mock_access_token_storage,
        sample_item_dto,
        sample_account_dto,
        mock_marketplace_api,
    ):
        """Test successful item publishing."""
        selling_service._validate_product_structure = AsyncMock(return_value=[])
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_access_token_storage.get.return_value = AuthToken(
            token="test_token", ttl=200
        )

        await selling_service.publish(
            sample_item_dto,
            sample_account_dto,
            "/path/to/image.jpg",
        )

        mock_api_factory.get.assert_called()

    @pytest.mark.asyncio
    async def test_publish_with_multiple_images(
        self,
        selling_service,
        mock_api_factory,
        mock_access_token_storage,
        sample_item_dto,
        sample_account_dto,
        mock_marketplace_api,
    ):
        """Test publishing with multiple images."""

        selling_service._validate_product_structure = Mock(return_value=[])
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_access_token_storage.get.return_value = AuthToken(
            token="test_token", ttl=200
        )

        await selling_service.publish(
            sample_item_dto,
            sample_account_dto,
            "/path/to/image1.jpg",
            "/path/to/image2.jpg",
        )

        mock_api_factory.get.assert_called()

    @pytest.mark.asyncio
    async def test_publish_marketplace_api_error(
        self,
        selling_service,
        mock_api_factory,
        mock_access_token_storage,
        sample_item_dto,
        sample_account_dto,
        mock_marketplace_api,
    ):
        """Test that MarketplaceAPIError is wrapped in InvalidCategory."""
        selling_service._validate_product_structure = Mock(return_value=[])
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_marketplace_api.publish.side_effect = MarketplaceAPIError("API error")
        mock_access_token_storage.get.return_value = AuthToken(
            token="test_token", ttl=200
        )

        with pytest.raises(SellingServiceError):
            await selling_service.publish(
                sample_item_dto,
                sample_account_dto,
            )


class TestSellingServiceValidateProductStructure:
    """Tests for SellingService._validate_product_structure method."""

    def test_validate_product_structure_success(
        self,
        selling_service,
        mock_api_factory,
        mock_marketplace_api,
    ):
        """Test successful product structure validation."""
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_marketplace_api.get_product_aspects.return_value = [
            AspectField(name="brand", data_type=AspectType.STR, is_required=True),
        ]

        aspects = selling_service._validate_product_structure(
            category_name="Electronics",
            aspects_data={"brand": "Apple"},
            marketplace="mockmarket",
        )

        assert isinstance(aspects, list)
        mock_marketplace_api.get_product_aspects.assert_called_once_with("Electronics")

    def test_validate_product_structure_with_multiple_aspects(
        self,
        selling_service,
        mock_api_factory,
        mock_marketplace_api,
    ):
        """Test validation with multiple aspects."""
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_marketplace_api.get_product_aspects.return_value = [
            AspectField(name="brand", data_type=AspectType.STR, is_required=True),
            AspectField(name="model", data_type=AspectType.STR, is_required=False),
            AspectField(name="year", data_type=AspectType.INT, is_required=False),
        ]

        aspects = selling_service._validate_product_structure(
            category_name="Electronics",
            aspects_data={"brand": "Sony", "model": "abc", "year": 2020},
            marketplace="mockmarket",
        )

        assert isinstance(aspects, list)

    def test_validate_product_structure_api_error(
        self,
        selling_service,
        mock_api_factory,
    ):
        """Test that MarketplaceAPIError is wrapped in SellingServiceError."""
        mock_api_factory.get.side_effect = MarketplaceAPIError("API error")

        with pytest.raises(SellingServiceError):
            selling_service._validate_product_structure(
                category_name="Electronics",
                aspects_data={"brand": "Apple"},
                marketplace="mockmarket",
            )

    def test_validate_product_structure_not_found_error(
        self,
        selling_service,
        mock_api_factory,
    ):
        """Test handling of CategoryNotFound."""
        mock_api = Mock()
        mock_api.get_product_aspects.side_effect = CategoryNotFound("Not found")
        mock_api_factory.get.return_value = mock_api

        with pytest.raises(InvalidCategory):
            selling_service._validate_product_structure(
                category_name="UnknownCategory",
                aspects_data={},
                marketplace="mockmarket",
            )

    def test_validate_product_structure_aspects_validation_error(
        self,
        selling_service,
        mock_api_factory,
        mock_marketplace_api,
    ):
        """Test handling of AspectsValidationError when required aspects are missing."""
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_marketplace_api.get_product_aspects.return_value = [
            AspectField(name="brand", data_type=AspectType.STR, is_required=True),
        ]

        with pytest.raises(SellingServiceError):
            selling_service._validate_product_structure(
                category_name="Electronics",
                aspects_data={},
                marketplace="mockmarket",
            )


class TestSellingServiceIntegration:
    """Integration tests for SellingService."""

    def test_validate_product_structure_creates_product_structure(
        self,
        selling_service,
        mock_api_factory,
        mock_marketplace_api,
    ):
        """Test that ProductStructure is correctly created during validation."""
        aspects_list = [
            AspectField(name="color", data_type=AspectType.STR, is_required=True),
        ]
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_marketplace_api.get_product_aspects.return_value = aspects_list

        result = selling_service._validate_product_structure(
            category_name="Electronics",
            aspects_data={"color": "Black"},
            marketplace="mockmarket",
        )

        assert isinstance(result, list)
        mock_marketplace_api.get_product_aspects.assert_called_once()


class TestSellingServiceErrorHandling:
    """Tests for error handling in SellingService."""

    @pytest.mark.asyncio
    async def test_publish_handles_marketplace_aspects_error(
        self,
        selling_service,
        mock_aspects_factory,
        sample_item_dto,
        sample_account_dto,
    ):
        """Test handling of marketplace aspects validation error."""
        mock_aspects_factory.get.return_value.validate.side_effect = Exception(
            "Validation failed"
        )

        with pytest.raises(Exception):
            await selling_service.publish(
                sample_item_dto,
                sample_account_dto,
            )

    def test_validate_product_structure_all_errors(
        self,
        selling_service,
        mock_api_factory,
    ):
        """Test that all expected errors are wrapped in SellingServiceError."""
        error_conditions = [
            MarketplaceAPIError("API error"),
            CategoryNotFound("Not found"),
        ]

        for error in error_conditions:
            mock_api = Mock()
            mock_api.get_product_aspects.side_effect = error
            mock_api_factory.get.return_value = mock_api

            with pytest.raises(SellingServiceError):
                selling_service._validate_product_structure(
                    category_name="Test",
                    aspects_data={},
                    marketplace="mockmarket",
                )
