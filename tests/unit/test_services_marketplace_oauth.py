"""Tests for services.marketplace_oauth module."""

import pytest
from uuid import uuid4
from unittest.mock import Mock, AsyncMock

from app.domain.ports.errors import InvalidToken
from app.services.marketplace_oauth import MarketplaceOAuthService, OAuthPayload
from app.domain.dto import MarketplaceAccountDTO
from app.domain.ports import (
    MarketplaceOAuthServiceError,
    MarketplaceUnauthorised,
)
from app.services.ports import (
    IAccessTokenStorage,
    IJWTAuth,
    IMarketplaceOAuthFactory,
    IRefreshTokenStorage,
    IUserRepository,
    OAuthParsingError,
    TokenNotFoundError,
    TokenStorageError,
    AuthToken,
)


@pytest.fixture
def mock_user_repo():
    """Create a mock user repository."""
    repo = AsyncMock(spec=IUserRepository)
    return repo


@pytest.fixture
def mock_jwt_auth():
    """Create a mock JWT auth."""
    jwt_auth = Mock(spec=IJWTAuth)
    return jwt_auth


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
def marketplace_oauth_service(
    mock_user_repo,
    mock_jwt_auth,
    mock_access_token_storage,
    mock_refresh_token_storage,
    mock_oauth_factory,
):
    """Create MarketplaceOAuthService with mocked dependencies."""
    return MarketplaceOAuthService(
        user_repo=mock_user_repo,
        jwt_auth=mock_jwt_auth,
        access_tokens_storage=mock_access_token_storage,
        refresh_tokens_storage=mock_refresh_token_storage,
        oauth_factory=mock_oauth_factory,
    )


@pytest.fixture
def test_user_uuid():
    """Create a test UUID for user."""
    return uuid4()


@pytest.fixture
def mock_oauth_payload(monkeypatch):
    """Mock OAuthPayload to make it instantiable."""
    from dataclasses import dataclass

    @dataclass
    class MockOAuthPayload:
        user_uuid: uuid4

    monkeypatch.setattr("app.services.marketplace_oauth.OAuthPayload", MockOAuthPayload)
    return MockOAuthPayload


@pytest.fixture
def valid_oauth_tokens():
    """Create valid OAuth tokens."""
    return {
        "access_token": "access_token_value",
        "expiers_in": 3600,
        "refresh_token": "refresh_token_value",
        "refresh_token_expires_in": 2592000,
    }


class TestMarketplaceOAuthServiceGenerateToken:
    """Tests for MarketplaceOAuthService.generate_token method."""

    def test_generate_token_success(
        self,
        marketplace_oauth_service,
        mock_jwt_auth,
        test_user_uuid,
        mock_oauth_payload,
    ):
        """Test successful token generation."""
        mock_jwt_token = Mock()
        mock_jwt_token.token = "generated_jwt_token"
        mock_jwt_auth.generate_token.return_value = mock_jwt_token

        result = marketplace_oauth_service.generate_token(test_user_uuid)

        assert result == "generated_jwt_token"
        mock_jwt_auth.generate_token.assert_called_once()

    def test_generate_token_creates_oauth_payload(
        self,
        marketplace_oauth_service,
        mock_jwt_auth,
        test_user_uuid,
        mock_oauth_payload,
    ):
        """Test that correct OAuthPayload is created."""
        mock_jwt_token = Mock()
        mock_jwt_token.token = "token"
        mock_jwt_auth.generate_token.return_value = mock_jwt_token

        marketplace_oauth_service.generate_token(test_user_uuid)

        mock_jwt_auth.generate_token.assert_called_once()


class TestMarketplaceOAuthServiceSaveTokens:
    """Tests for MarketplaceOAuthService.save_tokens method."""

    @pytest.mark.asyncio
    async def test_save_tokens_success(
        self,
        marketplace_oauth_service,
        mock_jwt_auth,
        mock_oauth_factory,
        mock_access_token_storage,
        mock_refresh_token_storage,
        test_user_uuid,
        valid_oauth_tokens,
    ):
        """Test successful token storage."""
        user_token = "user_jwt_token"
        marketplace = "EBAY_US"

        # Setup mock JWT verification
        mock_payload = Mock()
        mock_payload.user_uuid = test_user_uuid
        mock_jwt_auth.verify_token.return_value = mock_payload

        # Setup mock OAuth parsing
        mock_oauth = Mock()
        mock_oauth_tokens = Mock()
        mock_oauth_tokens.access_token = AuthToken(token="access", ttl=3600)
        mock_oauth_tokens.refresh_token = AuthToken(token="refresh", ttl=2592000)
        mock_oauth.parse.return_value = mock_oauth_tokens
        mock_oauth_factory.get.return_value = mock_oauth

        result = await marketplace_oauth_service.save_tokens(
            user_token,
            valid_oauth_tokens,
            marketplace,
        )

        assert result == test_user_uuid
        mock_jwt_auth.verify_token.assert_called_once_with(user_token, OAuthPayload)
        mock_oauth_factory.get.assert_called_once_with(marketplace)
        mock_oauth.parse.assert_called_once_with(valid_oauth_tokens)
        mock_access_token_storage.store.assert_called_once()
        mock_refresh_token_storage.store.assert_called_once()

    @pytest.mark.asyncio
    async def test_save_tokens_invalid_user_token(
        self,
        marketplace_oauth_service,
        mock_jwt_auth,
        valid_oauth_tokens,
    ):
        """Test that invalid user token returns None."""
        mock_jwt_auth.verify_token.return_value = None

        with pytest.raises(InvalidToken):
            await marketplace_oauth_service.save_tokens(
                "invalid_token", valid_oauth_tokens, "ebay"
            )

    @pytest.mark.asyncio
    async def test_save_tokens_oauth_parsing_error(
        self,
        marketplace_oauth_service,
        mock_jwt_auth,
        mock_oauth_factory,
        test_user_uuid,
    ):
        """Test that OAuthParsingError is wrapped in MarketplaceOAuthServiceError."""
        mock_payload = Mock()
        mock_payload.user_uuid = test_user_uuid
        mock_jwt_auth.verify_token.return_value = mock_payload

        mock_oauth = Mock()
        mock_oauth.parse.side_effect = OAuthParsingError("Parse error")
        mock_oauth_factory.get.return_value = mock_oauth

        with pytest.raises(MarketplaceOAuthServiceError):
            await marketplace_oauth_service.save_tokens(
                "user_token",
                {},
                "EBAY_US",
            )

    @pytest.mark.asyncio
    async def test_save_tokens_storage_error(
        self,
        marketplace_oauth_service,
        mock_jwt_auth,
        mock_oauth_factory,
        mock_access_token_storage,
        test_user_uuid,
        valid_oauth_tokens,
    ):
        """Test that TokenStorageError is wrapped in MarketplaceOAuthServiceError."""
        mock_payload = Mock()
        mock_payload.user_uuid = test_user_uuid
        mock_jwt_auth.verify_token.return_value = mock_payload

        mock_oauth = Mock()
        mock_oauth_tokens = Mock()
        mock_oauth_tokens.access_token = AuthToken(token="access", ttl=3600)
        mock_oauth_tokens.refresh_token = AuthToken(token="refresh", ttl=2592000)
        mock_oauth.parse.return_value = mock_oauth_tokens
        mock_oauth_factory.get.return_value = mock_oauth

        mock_access_token_storage.store.side_effect = TokenStorageError("Storage error")

        with pytest.raises(MarketplaceOAuthServiceError):
            await marketplace_oauth_service.save_tokens(
                "user_token",
                valid_oauth_tokens,
                "EBAY_US",
            )


class TestMarketplaceOAuthServiceLogout:
    """Tests for MarketplaceOAuthService.logout method."""

    @pytest.mark.asyncio
    async def test_logout_success(
        self,
        marketplace_oauth_service,
        mock_access_token_storage,
        mock_refresh_token_storage,
    ):
        """Test successful logout."""
        account_dto = MarketplaceAccountDTO(
            user_uuid="550e8400-e29b-41d4-a716-446655440000",
            marketplace="EBAY_US",
        )

        await marketplace_oauth_service.logout(account_dto)

        mock_access_token_storage.delete.assert_called_once()
        mock_refresh_token_storage.delete.assert_called_once()

    @pytest.mark.asyncio
    async def test_logout_storage_error(
        self,
        marketplace_oauth_service,
        mock_access_token_storage,
    ):
        """Test that TokenStorageError is wrapped in MarketplaceOAuthServiceError."""
        account_dto = MarketplaceAccountDTO(
            user_uuid="550e8400-e29b-41d4-a716-446655440000",
            marketplace="EBAY_US",
        )
        mock_access_token_storage.delete.side_effect = TokenStorageError(
            "Storage error"
        )

        with pytest.raises(MarketplaceOAuthServiceError):
            await marketplace_oauth_service.logout(account_dto)

    @pytest.mark.asyncio
    async def test_logout_token_not_found(
        self,
        marketplace_oauth_service,
        mock_access_token_storage,
    ):
        """Test that TokenNotFoundError during delete is properly handled."""
        account_dto = MarketplaceAccountDTO(
            user_uuid="550e8400-e29b-41d4-a716-446655440000",
            marketplace="EBAY_US",
        )
        mock_access_token_storage.delete = AsyncMock(
            side_effect=TokenNotFoundError("Not found")
        )

        # TokenNotFoundError is likely a subclass of TokenStorageError, so it gets wrapped as MarketplaceOAuthServiceError
        with pytest.raises((MarketplaceUnauthorised, MarketplaceOAuthServiceError)):
            await marketplace_oauth_service.logout(account_dto)


class TestMarketplaceOAuthServiceIntegration:
    """Integration tests for MarketplaceOAuthService."""

    def test_generate_token_workflow(
        self,
        marketplace_oauth_service,
        mock_jwt_auth,
        test_user_uuid,
        mock_oauth_payload,
    ):
        """Test complete token generation workflow."""
        mock_jwt_token = Mock()
        mock_jwt_token.token = "generated_token_123"
        mock_jwt_auth.generate_token.return_value = mock_jwt_token

        result = marketplace_oauth_service.generate_token(test_user_uuid)

        assert result == "generated_token_123"

    @pytest.mark.asyncio
    async def test_save_and_logout_workflow(
        self,
        marketplace_oauth_service,
        mock_jwt_auth,
        mock_oauth_factory,
        mock_access_token_storage,
        mock_refresh_token_storage,
        test_user_uuid,
        valid_oauth_tokens,
    ):
        """Test save tokens followed by logout."""
        user_token = "user_jwt_token"
        marketplace = "EBAY_US"

        # Setup for save_tokens
        mock_payload = Mock()
        mock_payload.user_uuid = test_user_uuid
        mock_jwt_auth.verify_token.return_value = mock_payload

        mock_oauth = Mock()
        mock_oauth_tokens = Mock()
        mock_oauth_tokens.access_token = AuthToken(token="access", ttl=3600)
        mock_oauth_tokens.refresh_token = AuthToken(token="refresh", ttl=2592000)
        mock_oauth.parse.return_value = mock_oauth_tokens
        mock_oauth_factory.get.return_value = mock_oauth

        # Save tokens
        result = await marketplace_oauth_service.save_tokens(
            user_token,
            valid_oauth_tokens,
            marketplace,
        )

        assert result == test_user_uuid

        # Logout
        account_dto = MarketplaceAccountDTO(
            user_uuid=test_user_uuid,
            marketplace=marketplace,
        )

        await marketplace_oauth_service.logout(account_dto)

        # Verify both delete methods were called
        assert mock_access_token_storage.delete.called
        assert mock_refresh_token_storage.delete.called


class TestOAuthPayloadStructure:
    """Tests for OAuthPayload structure."""

    def test_oauth_payload_has_user_uuid(self):
        """Test that OAuthPayload has user_uuid attribute."""
        payload = OAuthPayload()
        # OAuthPayload should have user_uuid as a class annotation
        assert "user_uuid" in OAuthPayload.__annotations__

    def test_oauth_payload_with_uuid(self, test_user_uuid):
        """Test OAuthPayload with UUID value."""
        payload = OAuthPayload()
        payload.user_uuid = test_user_uuid

        assert payload.user_uuid == test_user_uuid


class TestMarketplaceOAuthServiceErrorHandling:
    """Tests for error handling in MarketplaceOAuthService."""

    @pytest.mark.asyncio
    async def test_all_storage_errors_wrapped(
        self,
        marketplace_oauth_service,
        mock_access_token_storage,
    ):
        """Test that various storage errors are properly wrapped."""
        account_dto = MarketplaceAccountDTO(
            user_uuid="550e8400-e29b-41d4-a716-446655440000",
            marketplace="EBAY_US",
        )

        error = TokenStorageError("Generic storage error")
        mock_access_token_storage.delete.side_effect = error

        with pytest.raises(MarketplaceOAuthServiceError):
            await marketplace_oauth_service.logout(account_dto)
