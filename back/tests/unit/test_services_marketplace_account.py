import pytest
from unittest.mock import Mock, AsyncMock

from app.services.marketplace_account import MarketplaceAccountService
from app.services.common import MarketplaceTokenManager
from app.domain.dto import MarketplaceAccountDTO, AccountSettingsDTO
from app.domain.entities import AccountSettings
from app.domain.ports import (
    MarketplaceAuthorizationFailed,
    MarketplaceAccountServiceError,
)
from app.services.ports import (
    IMarketplaceAPIFactory,
    MarketplaceAPIError,
)
from app.services.mapping import FromEntity


@pytest.fixture
def mock_token_manager():
    manager = AsyncMock(spec=MarketplaceTokenManager)
    manager.access_token.return_value = "account_token"
    return manager


@pytest.fixture
def mock_api_factory():
    factory = Mock(spec=IMarketplaceAPIFactory)
    return factory


@pytest.fixture
def marketplace_account_service(mock_token_manager, mock_api_factory):
    return MarketplaceAccountService(
        token_manager=mock_token_manager,
        api_factory=mock_api_factory,
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

    account_settings = AccountSettings(
        settings=dict(
            fulfillment_policies=["Standard", "Express"],
            payment_policies=["CreditCard", "PayPal"],
            return_policies=["ReturnsAccepted", "NoReturns"],
            locations=["WarehouseA", "WarehouseB"],
        )
    )
    api.get_account_settings.return_value = account_settings

    return api


class TestMarketplaceAccountServiceFindSettings:
    @pytest.mark.asyncio
    async def test_find_settings_success(
        self,
        marketplace_account_service,
        mock_api_factory,
        mock_token_manager,
        sample_account_dto,
        mock_marketplace_api,
    ):
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_token_manager.access_token.return_value = "token"

        result = await marketplace_account_service.find_settings(sample_account_dto)

        assert isinstance(result, dict)
        mock_token_manager.access_token.assert_called_once()
        mock_api_factory.get.assert_called_once()
        mock_marketplace_api.get_account_settings.assert_called_once_with("token")

    @pytest.mark.asyncio
    async def test_find_settings_returns_correct_dto(
        self,
        marketplace_account_service,
        mock_api_factory,
        mock_token_manager,
        sample_account_dto,
        mock_marketplace_api,
    ):
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_token_manager.access_token.return_value = "token"

        result = await marketplace_account_service.find_settings(sample_account_dto)

        assert result == FromEntity.account_settings(
            mock_marketplace_api.get_account_settings.return_value
        )
        assert "payment_policies" in result
        assert "fulfillment_policies" in result
        assert "return_policies" in result
        assert "locations" in result

    @pytest.mark.asyncio
    async def test_find_settings_with_empty_policies(
        self,
        marketplace_account_service,
        mock_api_factory,
        mock_token_manager,
        sample_account_dto,
    ):
        mock_api = Mock()
        account_settings = AccountSettings(
            settings=dict(
                fulfillment_policies=[],
                payment_policies=[],
                return_policies=[],
                locations=[],
            )
        )
        mock_api.get_account_settings.return_value = account_settings
        mock_api_factory.get.return_value = mock_api
        mock_token_manager.access_token.return_value = "token"

        result = await marketplace_account_service.find_settings(sample_account_dto)

        assert FromEntity.account_settings(account_settings) == result

    @pytest.mark.asyncio
    async def test_find_settings_marketplace_api_error(
        self,
        marketplace_account_service,
        mock_api_factory,
        mock_token_manager,
        sample_account_dto,
    ):
        mock_api = Mock()
        mock_api.get_account_settings.side_effect = MarketplaceAPIError()
        mock_api_factory.get.return_value = mock_api
        mock_token_manager.access_token.return_value = "token"

        with pytest.raises(MarketplaceAccountServiceError):
            await marketplace_account_service.find_settings(sample_account_dto)

    @pytest.mark.asyncio
    async def test_find_settings_authorization_failed(
        self,
        marketplace_account_service,
        mock_api_factory,
        mock_token_manager,
        sample_account_dto,
    ):
        mock_token_manager.access_token.side_effect = MarketplaceAuthorizationFailed()

        with pytest.raises(MarketplaceAuthorizationFailed):
            await marketplace_account_service.find_settings(sample_account_dto)

    @pytest.mark.asyncio
    async def test_find_settings_multiple_items(
        self,
        marketplace_account_service,
        mock_api_factory,
        mock_token_manager,
        sample_account_dto,
        mock_marketplace_api,
    ):
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_token_manager.access_token.return_value = "token"

        account_settings = AccountSettings(
            settings=dict(
                fulfillment_policies=["Standard", "Express", "Overnight"],
                payment_policies=["CreditCard", "PayPal", "ApplePay"],
                return_policies=["ReturnsAccepted", "NoReturns", "ShortReturn"],
                locations=["WarehouseA", "WarehouseB", "WarehouseC"],
            )
        )
        mock_marketplace_api.get_account_settings.return_value = account_settings

        result = await marketplace_account_service.find_settings(sample_account_dto)

        assert result == FromEntity.account_settings(account_settings)


class TestMarketplaceAccountServiceErrorHandling:
    @pytest.mark.asyncio
    async def test_error_propagation_chain(
        self,
        marketplace_account_service,
        mock_api_factory,
        mock_token_manager,
        sample_account_dto,
    ):
        original_error = MarketplaceAPIError()
        mock_api = Mock()
        mock_api.get_account_settings.side_effect = original_error
        mock_api_factory.get.return_value = mock_api
        mock_token_manager.access_token.return_value = "token"

        with pytest.raises(MarketplaceAccountServiceError) as exc_info:
            await marketplace_account_service.find_settings(sample_account_dto)

        assert exc_info.value.__cause__ is original_error


class TestMarketplaceAccountServiceIntegration:
    @pytest.mark.asyncio
    async def test_find_settings_full_workflow(
        self,
        marketplace_account_service,
        mock_api_factory,
        mock_token_manager,
        sample_account_dto,
        mock_marketplace_api,
    ):
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_token_manager.access_token.return_value = "workflow_token"

        result = await marketplace_account_service.find_settings(sample_account_dto)

        assert result == FromEntity.account_settings(
            mock_marketplace_api.get_account_settings.return_value
        )
        mock_token_manager.access_token.assert_called_once()
        mock_api_factory.get.assert_called_once_with("ebay")
        mock_marketplace_api.get_account_settings.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_settings_called_multiple_times(
        self,
        marketplace_account_service,
        mock_api_factory,
        mock_token_manager,
        sample_account_dto,
        mock_marketplace_api,
    ):
        mock_api_factory.get.return_value = mock_marketplace_api
        mock_token_manager.access_token.return_value = "token"

        result1 = await marketplace_account_service.find_settings(sample_account_dto)
        result2 = await marketplace_account_service.find_settings(sample_account_dto)

        assert result1 == result2
        assert result1 == FromEntity.account_settings(
            mock_marketplace_api.get_account_settings.return_value
        )
        assert mock_token_manager.access_token.call_count == 2
        assert mock_api_factory.get.call_count == 2
