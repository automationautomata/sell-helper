import pytest
from unittest.mock import Mock, AsyncMock

from app.services.common import MarketplaceTokenManager
from app.domain.entities import MarketplaceAccount
from app.domain.ports import (
    MarketplaceAuthorizationFailed,
    MarketplaceUnauthorised,
)
from app.services.ports import (
    IAccessTokenStorage,
    IRefreshTokenStorage,
    IMarketplaceOAuthFactory,
    TokenStorageError,
    MarketplaceOAuthError,
    AuthToken,
)


@pytest.fixture
def mock_access_token_storage():
    storage = AsyncMock(spec=IAccessTokenStorage)
    return storage


@pytest.fixture
def mock_refresh_token_storage():
    storage = AsyncMock(spec=IRefreshTokenStorage)
    return storage


@pytest.fixture
def mock_oauth_factory():
    factory = Mock(spec=IMarketplaceOAuthFactory)
    return factory


@pytest.fixture
def token_manager(
    mock_access_token_storage,
    mock_refresh_token_storage,
    mock_oauth_factory,
):
    return MarketplaceTokenManager(
        access_token_storage=mock_access_token_storage,
        refresh_token_storage=mock_refresh_token_storage,
        oauth_factory=mock_oauth_factory,
        token_ttl_threshold=300,
    )


@pytest.fixture
def sample_account():
    return MarketplaceAccount(
        user_uuid="550e8400-e29b-41d4-a716-446655440000",
        marketplace="ebay",
    )


@pytest.fixture
def valid_access_token():
    return AuthToken(token="access_token", ttl=500)


@pytest.fixture
def expired_access_token():
    return AuthToken(token="expired_token_456", ttl=100)


@pytest.fixture
def valid_refresh_token():
    return AuthToken(token="refresh_token_789", ttl=2592000)


@pytest.fixture
def mock_oauth():
    oauth = AsyncMock()
    oauth.new_access_token = AsyncMock(
        return_value=AuthToken(token="new_access_token_111", ttl=3600)
    )
    return oauth


class TestMarketplaceTokenManagerAccessToken:
    @pytest.mark.asyncio
    async def test_access_token_from_storage_valid(
        self,
        token_manager,
        mock_access_token_storage,
        sample_account,
        valid_access_token,
    ):
        mock_access_token_storage.get.return_value = valid_access_token

        token = await token_manager.access_token(sample_account)

        assert token == "access_token"
        mock_access_token_storage.get.assert_called_once_with(sample_account)

    @pytest.mark.asyncio
    async def test_access_token_from_storage_expired_refresh(
        self,
        token_manager,
        mock_access_token_storage,
        mock_refresh_token_storage,
        mock_oauth_factory,
        sample_account,
        expired_access_token,
        valid_refresh_token,
        mock_oauth,
    ):
        mock_access_token_storage.get.return_value = expired_access_token
        mock_refresh_token_storage.get.return_value = valid_refresh_token
        mock_oauth_factory.get.return_value = mock_oauth

        token = await token_manager.access_token(sample_account)

        assert token == "new_access_token_111"
        mock_oauth.new_access_token.assert_called_once_with("refresh_token_789")
        mock_access_token_storage.store.assert_called_once()

    @pytest.mark.asyncio
    async def test_access_token_storage_error_uses_refresh(
        self,
        token_manager,
        mock_access_token_storage,
        mock_refresh_token_storage,
        mock_oauth_factory,
        sample_account,
        valid_refresh_token,
        mock_oauth,
    ):
        mock_access_token_storage.get.side_effect = TokenStorageError()
        mock_refresh_token_storage.get.return_value = valid_refresh_token
        mock_oauth_factory.get.return_value = mock_oauth

        token = await token_manager.access_token(sample_account)

        assert token == "new_access_token_111"
        mock_oauth.new_access_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_access_token_refresh_token_not_found(
        self,
        token_manager,
        mock_access_token_storage,
        mock_refresh_token_storage,
        sample_account,
    ):
        mock_access_token_storage.get.side_effect = TokenStorageError()
        mock_refresh_token_storage.get.return_value = None

        with pytest.raises(MarketplaceUnauthorised):
            await token_manager.access_token(sample_account)

    @pytest.mark.asyncio
    async def test_access_token_refresh_token_storage_error(
        self,
        token_manager,
        mock_access_token_storage,
        mock_refresh_token_storage,
        sample_account,
    ):
        mock_access_token_storage.get.side_effect = TokenStorageError()
        mock_refresh_token_storage.get.side_effect = TokenStorageError()

        with pytest.raises(MarketplaceAuthorizationFailed):
            await token_manager.access_token(sample_account)

    @pytest.mark.asyncio
    async def test_access_token_oauth_error_during_refresh(
        self,
        token_manager,
        mock_access_token_storage,
        mock_refresh_token_storage,
        mock_oauth_factory,
        sample_account,
        valid_refresh_token,
        mock_oauth,
    ):
        mock_access_token_storage.get.side_effect = TokenStorageError()
        mock_refresh_token_storage.get.return_value = valid_refresh_token
        mock_oauth_factory.get.return_value = mock_oauth
        mock_oauth.new_access_token.side_effect = MarketplaceOAuthError()

        with pytest.raises(MarketplaceAuthorizationFailed):
            await token_manager.access_token(sample_account)

    @pytest.mark.asyncio
    async def test_access_token_store_error_during_refresh(
        self,
        token_manager,
        mock_access_token_storage,
        mock_refresh_token_storage,
        mock_oauth_factory,
        sample_account,
        valid_refresh_token,
        mock_oauth,
    ):
        mock_access_token_storage.get.side_effect = TokenStorageError()
        mock_refresh_token_storage.get.return_value = valid_refresh_token
        mock_oauth_factory.get.return_value = mock_oauth
        mock_access_token_storage.store.side_effect = TokenStorageError()

        with pytest.raises(MarketplaceAuthorizationFailed):
            await token_manager.access_token(sample_account)

    @pytest.mark.asyncio
    async def test_access_token_with_none_refresh_token(
        self,
        token_manager,
        mock_access_token_storage,
        mock_refresh_token_storage,
        sample_account,
    ):
        mock_access_token_storage.get.side_effect = TokenStorageError()
        mock_refresh_token_storage.get.return_value = None

        with pytest.raises(MarketplaceUnauthorised):
            await token_manager.access_token(sample_account)


class TestMarketplaceTokenManagerThresholdLogic:
    @pytest.mark.asyncio
    async def test_access_token_above_threshold(
        self,
        token_manager,
        mock_access_token_storage,
        sample_account,
    ):
        good_token = AuthToken(token="good_token", ttl=500)
        mock_access_token_storage.get.return_value = good_token

        token = await token_manager.access_token(sample_account)

        assert token == "good_token"

    @pytest.mark.asyncio
    async def test_access_token_below_threshold(
        self,
        token_manager,
        mock_access_token_storage,
        mock_refresh_token_storage,
        mock_oauth_factory,
        sample_account,
        valid_refresh_token,
        mock_oauth,
    ):
        low_ttl_token = AuthToken(token="low_ttl_token", ttl=100)
        mock_access_token_storage.get.return_value = low_ttl_token
        mock_refresh_token_storage.get.return_value = valid_refresh_token
        mock_oauth_factory.get.return_value = mock_oauth

        token = await token_manager.access_token(sample_account)

        assert token == "new_access_token_111"
        mock_oauth.new_access_token.assert_called_once()

    @pytest.mark.asyncio
    async def test_access_token_exactly_at_threshold(
        self,
        token_manager,
        mock_access_token_storage,
        sample_account,
    ):
        at_threshold_token = AuthToken(token="at_threshold_token", ttl=300)
        mock_access_token_storage.get.return_value = at_threshold_token

        token = await token_manager.access_token(sample_account)

        assert token == "at_threshold_token"


class TestMarketplaceTokenManagerMultipleAccounts:
    @pytest.mark.asyncio
    async def test_different_accounts_separate_tokens(
        self,
        token_manager,
        mock_access_token_storage,
    ):
        account1 = MarketplaceAccount(
            user_uuid="550e8400-e29b-41d4-a716-446655440000",
            marketplace="ebay",
        )
        account2 = MarketplaceAccount(
            user_uuid="550e8400-e29b-41d4-a716-446655440001",
            marketplace="ebay",
        )

        token1 = AuthToken(token="token_user1", ttl=500)
        token2 = AuthToken(token="token_user2", ttl=500)

        mock_access_token_storage.get.side_effect = [token1, token2]

        result1 = await token_manager.access_token(account1)
        result2 = await token_manager.access_token(account2)

        assert result1 == "token_user1"
        assert result2 == "token_user2"
        assert mock_access_token_storage.get.call_count == 2

    @pytest.mark.asyncio
    async def test_multiple_marketplaces(
        self,
        token_manager,
        mock_access_token_storage,
    ):
        account_ebay = MarketplaceAccount(
            user_uuid="550e8400-e29b-41d4-a716-446655440000",
            marketplace="ebay",
        )
        account_amazon = MarketplaceAccount(
            user_uuid="550e8400-e29b-41d4-a716-446655440000",
            marketplace="amazon",
        )

        token_ebay = AuthToken(token="ebay_token", ttl=500)
        token_amazon = AuthToken(token="amazon_token", ttl=500)

        mock_access_token_storage.get.side_effect = [token_ebay, token_amazon]

        result_ebay = await token_manager.access_token(account_ebay)
        result_amazon = await token_manager.access_token(account_amazon)

        assert result_ebay == "ebay_token"
        assert result_amazon == "amazon_token"


class TestMarketplaceTokenManagerErrorChaining:
    @pytest.mark.asyncio
    async def test_oauth_error_chaining(
        self,
        token_manager,
        mock_access_token_storage,
        mock_refresh_token_storage,
        mock_oauth_factory,
        sample_account,
        valid_refresh_token,
        mock_oauth,
    ):
        original_error = MarketplaceOAuthError()
        mock_access_token_storage.get.side_effect = TokenStorageError()
        mock_refresh_token_storage.get.return_value = valid_refresh_token
        mock_oauth_factory.get.return_value = mock_oauth
        mock_oauth.new_access_token.side_effect = original_error

        with pytest.raises(MarketplaceAuthorizationFailed) as exc_info:
            await token_manager.access_token(sample_account)

        assert exc_info.value.__cause__ is original_error

    @pytest.mark.asyncio
    async def test_storage_error_chaining(
        self,
        token_manager,
        mock_access_token_storage,
        mock_refresh_token_storage,
        sample_account,
    ):
        original_error = TokenStorageError()
        mock_access_token_storage.get.side_effect = TokenStorageError()
        mock_refresh_token_storage.get.side_effect = original_error

        with pytest.raises(MarketplaceAuthorizationFailed) as exc_info:
            await token_manager.access_token(sample_account)

        assert exc_info.value.__cause__ is original_error


class TestMarketplaceTokenManagerIntegration:
    @pytest.mark.asyncio
    async def test_complete_refresh_workflow(
        self,
        token_manager,
        mock_access_token_storage,
        mock_refresh_token_storage,
        mock_oauth_factory,
        sample_account,
        valid_refresh_token,
        mock_oauth,
    ):
        expired_token = AuthToken(token="expired", ttl=100)
        mock_access_token_storage.get.return_value = expired_token
        mock_refresh_token_storage.get.return_value = valid_refresh_token
        mock_oauth_factory.get.return_value = mock_oauth

        token = await token_manager.access_token(sample_account)

        assert token == "new_access_token_111"
        mock_access_token_storage.get.assert_called_once_with(sample_account)
        mock_refresh_token_storage.get.assert_called_once_with(sample_account)
        mock_oauth.new_access_token.assert_called_once_with("refresh_token_789")
        mock_access_token_storage.store.assert_called_once()

    @pytest.mark.asyncio
    async def test_cached_token_reuse(
        self,
        token_manager,
        mock_access_token_storage,
        sample_account,
        valid_access_token,
    ):
        mock_access_token_storage.get.return_value = valid_access_token

        token1 = await token_manager.access_token(sample_account)
        token2 = await token_manager.access_token(sample_account)

        assert token1 == token2 == "access_token"
        assert mock_access_token_storage.get.call_count == 2

    @pytest.mark.asyncio
    async def test_fallback_to_refresh_on_no_access_token(
        self,
        token_manager,
        mock_access_token_storage,
        mock_refresh_token_storage,
        mock_oauth_factory,
        sample_account,
        valid_refresh_token,
        mock_oauth,
    ):
        mock_access_token_storage.get.side_effect = TokenStorageError()
        mock_refresh_token_storage.get.return_value = valid_refresh_token
        mock_oauth_factory.get.return_value = mock_oauth

        token = await token_manager.access_token(sample_account)

        assert token == "new_access_token_111"

    @pytest.mark.asyncio
    async def test_all_failure_paths_covered(
        self,
        token_manager,
        mock_access_token_storage,
        mock_refresh_token_storage,
        mock_oauth_factory,
        sample_account,
    ):
        error_scenarios = [
            {
                "name": "No refresh token",
                "access_error": TokenStorageError(),
                "refresh_token": None,
                "expected_error": MarketplaceUnauthorised,
            },
            {
                "name": "Refresh token storage error",
                "access_error": TokenStorageError(),
                "refresh_error": TokenStorageError(),
                "expected_error": MarketplaceAuthorizationFailed,
            },
        ]

        for scenario in error_scenarios:
            mock_access_token_storage.reset_mock()
            mock_refresh_token_storage.reset_mock()

            if "access_error" in scenario:
                mock_access_token_storage.get.side_effect = scenario["access_error"]

            if "refresh_token" in scenario:
                mock_refresh_token_storage.get.return_value = scenario["refresh_token"]

            if "refresh_error" in scenario:
                mock_refresh_token_storage.get.side_effect = scenario["refresh_error"]

            with pytest.raises(scenario["expected_error"]):
                await token_manager.access_token(sample_account)
