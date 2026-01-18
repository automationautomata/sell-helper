import pytest
from unittest.mock import Mock, AsyncMock

from app.domain.ports.errors import (
    InvalidCategory,
    InvalidMarketplaceAspects,
    InvalidProductAspects,
)
from app.domain.ports import MarketplaceAuthorizationFailed, SellingServiceError
from app.services.selling import SellingService
from app.services.common import MarketplaceTokenManager
from app.domain.dto import ItemDTO, MarketplaceAccountDTO
from app.domain.entities import AspectField, AspectType
from app.services.ports import (
    CategoryNotFound,
    IMarketplaceAPIFactory,
    IMarketplaceAspectsFactory,
    MarketplaceAPIError,
)
from app.domain.entities.errors import AspectsValidationError


class MockMarketplaceAspects:
    @staticmethod
    def validate(data):
        return Mock(
            marketplace="ebay",
            policies=Mock(
                fulfillment_policy="Standard",
                payment_policy="CreditCard",
                return_policy="ReturnsAccepted",
                location="WarehouseA",
            ),
            package=Mock(
                weight_value=2.5,
                weight_unit="KG",
                dimension_length=10,
                dimension_width=8,
                dimension_height=5,
                dimension_unit="CM",
            ),
            condition="NEW",
            condition_description="Brand new item",
        )


@pytest.fixture
def mock_api_factory():
    factory = Mock(spec=IMarketplaceAPIFactory)
    return factory


@pytest.fixture
def mock_token_manager():
    manager = AsyncMock(spec=MarketplaceTokenManager)
    manager.access_token.return_value = "test_access_token"
    return manager


@pytest.fixture
def mock_aspects_factory():
    factory = Mock(spec=IMarketplaceAspectsFactory)
    factory.get.return_value = MockMarketplaceAspects
    return factory


@pytest.fixture
def selling_service(
    mock_api_factory,
    mock_token_manager,
    mock_aspects_factory,
):
    return SellingService(
        api_factory=mock_api_factory,
        token_manager=mock_token_manager,
        type_factory=mock_aspects_factory,
    )


@pytest.fixture
def sample_item_dto():
    return ItemDTO(
        title="Test iPhone 13",
        description="Latest iPhone model with advanced camera",
        price=999.99,
        currency="USD",
        country="US",
        category="Electronics > Mobile Phones",
        product_aspects={
            "brand": "Apple",
            "model": "iPhone 13",
            "color": "Black",
        },
        marketplace_aspects_data={
            "marketplace": "ebay",
            "condition": "NEW",
            "location": "WarehouseA",
        },
        quantity=10,
    )


@pytest.fixture
def sample_account_dto():
    return MarketplaceAccountDTO(
        user_uuid="550e8400-e29b-41d4-a716-446655440000",
        marketplace="ebay",
    )


@pytest.fixture
def mock_marketplace_api():
    api = Mock()
    api.get_product_aspects.return_value = [
        AspectField(
            name="brand",
            data_type=AspectType.STR,
            is_required=True,
            allowed_values=frozenset(["Apple", "Samsung", "Google"]),
        ),
        AspectField(
            name="model",
            data_type=AspectType.STR,
            is_required=True,
        ),
        AspectField(
            name="color",
            data_type=AspectType.STR,
            is_required=False,
        ),
    ]
    api.publish = Mock()
    return api


class TestSellingServicePublish:
    @pytest.mark.asyncio
    async def test_publish_authorization_failure_reraised(
        self,
        selling_service,
        mock_token_manager,
        sample_item_dto,
        sample_account_dto,
        mock_api_factory,
        mock_marketplace_api,
    ):
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_token_manager.access_token.side_effect = MarketplaceAuthorizationFailed()

        with pytest.raises(MarketplaceAuthorizationFailed):
            await selling_service.publish(sample_item_dto, sample_account_dto)


class TestSellingServiceValidateProductStructure:
    def test_validate_product_structure_success(
        self, selling_service, mock_api_factory, mock_marketplace_api
    ):
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_marketplace_api.get_product_aspects.return_value = [
            AspectField(
                name="brand",
                data_type=AspectType.STR,
                is_required=True,
                allowed_values=frozenset(["Apple", "Samsung"]),
            ),
            AspectField(
                name="model",
                data_type=AspectType.STR,
                is_required=True,
            ),
        ]

        aspects = selling_service._validate_product_structure(
            category_name="Electronics > Mobile Phones",
            aspects_data={"brand": "Apple", "model": "iPhone 13"},
            marketplace="ebay",
        )

        assert isinstance(aspects, list)
        mock_marketplace_api.get_product_aspects.assert_called_once_with(
            "Electronics > Mobile Phones"
        )

    def test_validate_product_structure_api_error(
        self, selling_service, mock_api_factory
    ):
        mock_api_factory.get.side_effect = MarketplaceAPIError()

        with pytest.raises(SellingServiceError):
            selling_service._validate_product_structure(
                category_name="Electronics",
                aspects_data={"brand": "Apple"},
                marketplace="ebay",
            )

    def test_validate_product_structure_category_not_found(
        self, selling_service, mock_api_factory
    ):
        mock_api = Mock()
        mock_api.get_product_aspects.side_effect = CategoryNotFound()
        mock_api_factory.get.return_value = mock_api

        with pytest.raises(InvalidCategory):
            selling_service._validate_product_structure(
                category_name="UnknownCategory", aspects_data={}, marketplace="ebay"
            )


class TestSellingServiceIntegration:
    def test_validate_product_structure_creates_product_structure(
        self, selling_service, mock_api_factory, mock_marketplace_api
    ):
        aspects_list = [
            AspectField(name="color", data_type=AspectType.STR, is_required=True),
            AspectField(name="size", data_type=AspectType.STR, is_required=True),
        ]
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_marketplace_api.get_product_aspects.return_value = aspects_list

        result = selling_service._validate_product_structure(
            category_name="Electronics",
            aspects_data={"color": "Black", "size": "Large"},
            marketplace="ebay",
        )

        assert isinstance(result, list)
        mock_marketplace_api.get_product_aspects.assert_called_once()


class TestSellingServiceErrorHandling:
    @pytest.mark.asyncio
    async def test_publish_marketplace_aspects_none_raises_error(
        self, selling_service, mock_aspects_factory, sample_item_dto, sample_account_dto
    ):
        marketplace_aspects_mock = Mock()
        marketplace_aspects_mock.validate.return_value = None
        mock_aspects_factory.get.return_value = marketplace_aspects_mock

        with pytest.raises(InvalidMarketplaceAspects):
            await selling_service.publish(sample_item_dto, sample_account_dto)

    def test_validate_product_structure_error_mapping(
        self, selling_service, mock_api_factory
    ):
        error_conditions = [
            (MarketplaceAPIError(), SellingServiceError),
            (CategoryNotFound(), InvalidCategory),
            (AspectsValidationError(), InvalidProductAspects),
        ]

        for error, expected_exception in error_conditions:
            mock_api = Mock()
            mock_api.get_product_aspects.side_effect = error
            mock_api_factory.get.return_value = mock_api

            with pytest.raises(expected_exception):
                selling_service._validate_product_structure(
                    category_name="Test",
                    aspects_data={},
                    marketplace="ebay",
                )
