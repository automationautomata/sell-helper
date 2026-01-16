"""Tests for infrastructure.oauth module."""

import pytest
from datetime import timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.infrastructure.oauth import EbayOAuth
from app.services.ports import (
    AuthToken,
    MarketplaceOAuthError,
    OAuth2Tokens,
    OAuthParsingError,
)
from app.infrastructure.api_clients.ebay import EbayAuthError


@pytest.fixture
def mock_ebay_user_client():
    """Create a mock EbayUserClient."""
    client = AsyncMock()
    return client


@pytest.fixture
def ebay_oauth(mock_ebay_user_client):
    """Create EbayOAuth instance with mocked client."""
    return EbayOAuth(
        client=mock_ebay_user_client,
        refresh_token_ttl=int(timedelta(weeks=4 * 18).total_seconds()),
    )


@pytest.fixture
def valid_token_response():
    """Create a valid token response from eBay API."""
    response = Mock()
    response.access_token = "test_access_token_12345"
    response.expires_in = 3600
    return response


@pytest.fixture
def valid_oauth_data():
    """Create valid OAuth2 token data."""
    return {
        "access_token": "access_token_value",
        "expiers_in": 3600,
        "refresh_token": "refresh_token_value",
        "refresh_token_expires_in": int(timedelta(weeks=4 * 18).total_seconds()),
    }


class TestEbayOAuthNewAccessToken:
    """Tests for EbayOAuth.new_access_token method."""

    @pytest.mark.asyncio
    async def test_new_access_token_success(
        self, ebay_oauth, mock_ebay_user_client, valid_token_response
    ):
        """Test successful access token refresh."""
        mock_ebay_user_client.refresh_token.return_value = valid_token_response

        result = await ebay_oauth.new_access_token("refresh_token_123")

        assert isinstance(result, AuthToken)
        assert result.token == "test_access_token_12345"
        assert result.ttl == 3600
        mock_ebay_user_client.refresh_token.assert_called_once_with(
            refresh_token="refresh_token_123"
        )

    @pytest.mark.asyncio
    async def test_new_access_token_ebay_auth_error(
        self, ebay_oauth, mock_ebay_user_client
    ):
        """Test that EbayAuthError is wrapped in MarketplaceOAuthError."""
        mock_ebay_user_client.refresh_token.side_effect = EbayAuthError("Auth failed")

        with pytest.raises(MarketplaceOAuthError):
            await ebay_oauth.new_access_token("invalid_token")

    @pytest.mark.asyncio
    async def test_new_access_token_with_expired_token(
        self, ebay_oauth, mock_ebay_user_client
    ):
        """Test access token refresh with expired refresh token."""
        mock_ebay_user_client.refresh_token.side_effect = EbayAuthError("Token expired")

        with pytest.raises(MarketplaceOAuthError):
            await ebay_oauth.new_access_token("expired_refresh_token")

    @pytest.mark.asyncio
    async def test_new_access_token_preserves_ttl(
        self, ebay_oauth, mock_ebay_user_client
    ):
        """Test that TTL is correctly set in returned token."""
        token_response = Mock()
        token_response.access_token = "new_token"
        token_response.expires_in = 7200
        mock_ebay_user_client.refresh_token.return_value = token_response

        result = await ebay_oauth.new_access_token("refresh_token")

        assert result.ttl == 7200


class TestEbayOAuthParse:
    """Tests for EbayOAuth.parse method."""

    def test_parse_valid_oauth_data(self, ebay_oauth, valid_oauth_data):
        """Test parsing valid OAuth data."""
        result = ebay_oauth.parse(valid_oauth_data)

        assert isinstance(result, OAuth2Tokens)
        assert isinstance(result.access_token, AuthToken)
        assert isinstance(result.refresh_token, AuthToken)
        assert result.access_token.token == "access_token_value"
        assert result.access_token.ttl == 3600
        assert result.refresh_token.token == "refresh_token_value"

    def test_parse_oauth_data_with_custom_refresh_ttl(self, ebay_oauth):
        """Test parsing OAuth data with custom refresh token TTL."""
        data = {
            "access_token": "access_token",
            "expiers_in": 3600,
            "refresh_token": "refresh_token",
            "refresh_token_expires_in": 7776000,  # 90 days
        }

        result = ebay_oauth.parse(data)

        assert result.refresh_token.ttl == 7776000

    def test_parse_oauth_data_uses_default_ttl_when_missing(self, ebay_oauth):
        """Test that default TTL is used when refresh_token_expires_in is missing."""
        data = {
            "access_token": "access_token",
            "expiers_in": 3600,
            "refresh_token": "refresh_token",
        }

        result = ebay_oauth.parse(data)

        assert result.refresh_token.ttl == ebay_oauth.refresh_token_ttl

    def test_parse_missing_access_token_raises_error(self, ebay_oauth):
        """Test that missing access_token raises OAuthParsingError."""
        data = {
            "expiers_in": 3600,
            "refresh_token": "refresh_token",
        }

        with pytest.raises(OAuthParsingError):
            ebay_oauth.parse(data)

    def test_parse_missing_expiries_in_raises_error(self, ebay_oauth):
        """Test that missing expiers_in raises OAuthParsingError."""
        data = {
            "access_token": "access_token",
            "refresh_token": "refresh_token",
        }

        with pytest.raises(OAuthParsingError):
            ebay_oauth.parse(data)

    def test_parse_missing_refresh_token_raises_error(self, ebay_oauth):
        """Test that missing refresh_token raises OAuthParsingError."""
        data = {
            "access_token": "access_token",
            "expiers_in": 3600,
        }

        with pytest.raises(OAuthParsingError):
            ebay_oauth.parse(data)

    def test_parse_empty_dict_raises_error(self, ebay_oauth):
        """Test that empty dict raises OAuthParsingError."""
        with pytest.raises(OAuthParsingError):
            ebay_oauth.parse({})

    def test_parse_malformed_ttl_raises_error(self, ebay_oauth):
        """Test that malformed TTL value raises appropriate error."""
        data = {
            "access_token": "access_token",
            "expiers_in": "not_a_number",  # Should be int
            "refresh_token": "refresh_token",
        }

        # This should raise ValueError (from int() conversion)
        with pytest.raises((OAuthParsingError, TypeError, ValueError)):
            ebay_oauth.parse(data)


class TestEbayOAuthConfiguration:
    """Tests for EbayOAuth configuration and initialization."""

    def test_ebay_oauth_default_refresh_token_ttl(self, mock_ebay_user_client):
        """Test that default refresh token TTL is set correctly."""
        oauth = EbayOAuth(client=mock_ebay_user_client)

        expected_ttl = int(timedelta(weeks=4 * 18).total_seconds())
        assert oauth.refresh_token_ttl == expected_ttl

    def test_ebay_oauth_custom_refresh_token_ttl(self, mock_ebay_user_client):
        """Test that custom refresh token TTL can be set."""
        custom_ttl = 7776000  # 90 days
        oauth = EbayOAuth(client=mock_ebay_user_client, refresh_token_ttl=custom_ttl)

        assert oauth.refresh_token_ttl == custom_ttl

    def test_ebay_oauth_client_stored(self, mock_ebay_user_client):
        """Test that client is properly stored."""
        oauth = EbayOAuth(client=mock_ebay_user_client)

        assert oauth.client is mock_ebay_user_client


class TestEbayOAuthIntegration:
    """Integration tests for EbayOAuth."""

    @pytest.mark.asyncio
    async def test_full_token_refresh_workflow(self, mock_ebay_user_client):
        """Test complete token refresh workflow."""
        token_response = Mock()
        token_response.access_token = "new_access_token"
        token_response.expires_in = 3600
        mock_ebay_user_client.refresh_token.return_value = token_response

        oauth = EbayOAuth(client=mock_ebay_user_client)

        result = await oauth.new_access_token("refresh_token")

        assert result.token == "new_access_token"
        assert result.ttl == 3600

    def test_parse_and_create_oauth_tokens(self, ebay_oauth):
        """Test parsing OAuth data and creating OAuth2Tokens."""
        data = {
            "access_token": "access_123",
            "expiers_in": 3600,
            "refresh_token": "refresh_456",
            "refresh_token_expires_in": 2592000,
        }

        oauth_tokens = ebay_oauth.parse(data)

        assert oauth_tokens.access_token.token == "access_123"
        assert oauth_tokens.refresh_token.token == "refresh_456"
        assert oauth_tokens.access_token.ttl == 3600
        assert oauth_tokens.refresh_token.ttl == 2592000
