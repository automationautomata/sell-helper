"""Tests for infrastructure.access_token_storage module."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from redis.asyncio import Redis, RedisError

from app.infrastructure.access_token_storage import RedisAccessTokenStorage
from app.domain.entities import MarketplaceAccount
from app.services.ports import (
    AuthToken,
    AcessTokenStorageError,
    TokenExpiredError,
    TokenStorageError,
)


@pytest.fixture
def mock_redis():
    """Create a mock Redis instance."""
    redis = AsyncMock(spec=Redis)
    redis.set = AsyncMock(return_value=None)
    redis.get = AsyncMock(return_value=None)
    redis.delete = AsyncMock(return_value=0)
    return redis


@pytest.fixture
def access_token_storage(mock_redis):
    """Create RedisAccessTokenStorage with mocked Redis."""
    return RedisAccessTokenStorage(redis=mock_redis)


@pytest.fixture
def test_account():
    """Create a test MarketplaceAccount."""
    return MarketplaceAccount(
        user_uuid="550e8400-e29b-41d4-a716-446655440000",
        marketplace="EBAY_US",
    )


@pytest.fixture
def auth_token():
    """Create a test AuthToken."""
    return AuthToken(token="test_token_12345", ttl=3600)


class TestRedisAccessTokenStorageToKey:
    """Tests for RedisAccessTokenStorage._to_key method."""

    def test_to_key_format(self, test_account):
        """Test that key is formatted correctly."""
        key = RedisAccessTokenStorage._to_key(test_account)

        assert isinstance(key, str)
        assert test_account.user_uuid in key
        assert test_account.marketplace in key
        assert key == f"{test_account.user_uuid}{test_account.marketplace}"

    def test_to_key_with_different_accounts(self):
        """Test that different accounts generate different keys."""
        account1 = MarketplaceAccount(
            user_uuid="550e8400-e29b-41d4-a716-446655440000",
            marketplace="EBAY_US",
        )
        account2 = MarketplaceAccount(
            user_uuid="550e8400-e29b-41d4-a716-446655440001",
            marketplace="EBAY_UK",
        )

        key1 = RedisAccessTokenStorage._to_key(account1)
        key2 = RedisAccessTokenStorage._to_key(account2)

        assert key1 != key2

    def test_to_key_consistency(self, test_account):
        """Test that same account always generates same key."""
        key1 = RedisAccessTokenStorage._to_key(test_account)
        key2 = RedisAccessTokenStorage._to_key(test_account)

        assert key1 == key2


class TestRedisAccessTokenStorageStore:
    """Tests for RedisAccessTokenStorage.store method."""

    @pytest.mark.asyncio
    async def test_store_success(
        self, access_token_storage, mock_redis, test_account, auth_token
    ):
        """Test successful token storage."""
        await access_token_storage.store(test_account, auth_token)

        expected_key = RedisAccessTokenStorage._to_key(test_account)
        mock_redis.set.assert_called_once_with(
            expected_key, auth_token.token, ex=auth_token.ttl
        )

    @pytest.mark.asyncio
    async def test_store_with_zero_ttl_raises_error(
        self, access_token_storage, test_account
    ):
        """Test that zero TTL raises TokenStorageError."""
        invalid_token = AuthToken(token="test_token", ttl=0)

        with pytest.raises(TokenStorageError, match="TTL must be positive"):
            await access_token_storage.store(test_account, invalid_token)

    @pytest.mark.asyncio
    async def test_store_with_negative_ttl_raises_error(
        self, access_token_storage, test_account
    ):
        """Test that negative TTL raises TokenStorageError."""
        invalid_token = AuthToken(token="test_token", ttl=-100)

        with pytest.raises(TokenStorageError, match="TTL must be positive"):
            await access_token_storage.store(test_account, invalid_token)

    @pytest.mark.asyncio
    async def test_store_redis_error_wrapped(
        self, access_token_storage, mock_redis, test_account, auth_token
    ):
        """Test that RedisError is wrapped in AcessTokenStorageError."""
        mock_redis.set.side_effect = RedisError("Redis connection failed")

        with pytest.raises(
            AcessTokenStorageError, match="Failed to store access token"
        ):
            await access_token_storage.store(test_account, auth_token)

    @pytest.mark.asyncio
    async def test_store_with_large_ttl(
        self, access_token_storage, mock_redis, test_account
    ):
        """Test storing token with large TTL."""
        large_ttl_token = AuthToken(token="test_token", ttl=7776000)  # 90 days

        await access_token_storage.store(test_account, large_ttl_token)

        expected_key = RedisAccessTokenStorage._to_key(test_account)
        mock_redis.set.assert_called_once_with(expected_key, "test_token", ex=7776000)


class TestRedisAccessTokenStorageGet:
    """Tests for RedisAccessTokenStorage.get method."""

    @pytest.mark.asyncio
    async def test_get_existing_token_success(
        self, access_token_storage, mock_redis, test_account, auth_token
    ):
        """Test successful token retrieval."""
        mock_redis.get = AsyncMock(return_value=auth_token.token)
        mock_redis.ttl = AsyncMock(return_value=auth_token.ttl)

        result = await access_token_storage.get(test_account)

        assert isinstance(result, AuthToken)
        assert result.token == auth_token.token
        assert result.ttl == auth_token.ttl

    @pytest.mark.asyncio
    async def test_get_nonexistent_token_returns_none(
        self, access_token_storage, mock_redis, test_account
    ):
        """Test that getting nonexistent token returns None."""
        mock_redis.get = AsyncMock(return_value=None)

        result = await access_token_storage.get(test_account)

        assert result is None
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_expired_token_raises_error(
        self, access_token_storage, mock_redis, test_account
    ):
        """Test that expired token raises TokenExpiredError."""
        mock_redis.get = AsyncMock(return_value="expired_token")
        mock_redis.ttl = AsyncMock(return_value=-1)  # Token has expired

        with pytest.raises(TokenExpiredError):
            await access_token_storage.get(test_account)

    @pytest.mark.asyncio
    async def test_get_token_with_zero_ttl_raises_error(
        self, access_token_storage, mock_redis, test_account
    ):
        """Test that token with zero TTL raises TokenExpiredError."""
        mock_redis.get = AsyncMock(return_value="token")
        mock_redis.ttl = AsyncMock(return_value=0)

        with pytest.raises(TokenExpiredError):
            await access_token_storage.get(test_account)

    @pytest.mark.asyncio
    async def test_get_redis_error_wrapped(
        self, access_token_storage, mock_redis, test_account
    ):
        """Test that RedisError during get is wrapped in AcessTokenStorageError."""
        mock_redis.get.side_effect = RedisError("Redis connection failed")

        with pytest.raises(AcessTokenStorageError):
            await access_token_storage.get(test_account)

    @pytest.mark.asyncio
    async def test_get_calls_correct_methods(
        self, access_token_storage, mock_redis, test_account
    ):
        """Test that correct Redis methods are called."""
        mock_redis.get = AsyncMock(return_value="token")
        mock_redis.ttl = AsyncMock(return_value=3600)

        await access_token_storage.get(test_account)

        expected_key = RedisAccessTokenStorage._to_key(test_account)
        mock_redis.get.assert_called_once_with(expected_key)
        mock_redis.ttl.assert_called_once_with(expected_key)


class TestRedisAccessTokenStorageDelete:
    """Tests for RedisAccessTokenStorage.delete method."""

    @pytest.mark.asyncio
    async def test_delete_success(self, access_token_storage, mock_redis, test_account):
        """Test successful token deletion."""
        await access_token_storage.delete(test_account)

        expected_key = RedisAccessTokenStorage._to_key(test_account)
        mock_redis.delete.assert_called_once_with(expected_key)

    @pytest.mark.asyncio
    async def test_delete_redis_error_wrapped(
        self, access_token_storage, mock_redis, test_account
    ):
        """Test that RedisError during delete is wrapped in AcessTokenStorageError."""
        mock_redis.delete.side_effect = RedisError("Redis connection failed")

        with pytest.raises(
            AcessTokenStorageError, match="Failed to delete access token"
        ):
            await access_token_storage.delete(test_account)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_token(
        self, access_token_storage, mock_redis, test_account
    ):
        """Test deleting non-existent token (should not raise)."""
        mock_redis.delete = AsyncMock(return_value=0)  # Key didn't exist

        await access_token_storage.delete(test_account)

        mock_redis.delete.assert_called_once()


class TestRedisAccessTokenStorageIntegration:
    """Integration tests for RedisAccessTokenStorage."""

    @pytest.mark.asyncio
    async def test_store_and_get_workflow(
        self, access_token_storage, mock_redis, test_account
    ):
        """Test complete store and get workflow."""
        token = AuthToken(token="integration_test_token", ttl=3600)

        # Store
        await access_token_storage.store(test_account, token)

        # Get
        mock_redis.get = AsyncMock(return_value=token.token)
        mock_redis.ttl = AsyncMock(return_value=token.ttl)

        result = await access_token_storage.get(test_account)

        assert result.token == token.token
        assert result.ttl == token.ttl

    @pytest.mark.asyncio
    async def test_store_and_delete_workflow(
        self, access_token_storage, mock_redis, test_account
    ):
        """Test complete store and delete workflow."""
        token = AuthToken(token="integration_test_token", ttl=3600)

        await access_token_storage.store(test_account, token)
        await access_token_storage.delete(test_account)

        expected_key = RedisAccessTokenStorage._to_key(test_account)
        assert mock_redis.set.called
        assert mock_redis.delete.called
        mock_redis.delete.assert_called_with(expected_key)

    @pytest.mark.asyncio
    async def test_multiple_accounts_isolation(self, mock_redis):
        """Test that different accounts don't interfere with each other."""
        storage = RedisAccessTokenStorage(redis=mock_redis)

        account1 = MarketplaceAccount(
            user_uuid="550e8400-e29b-41d4-a716-446655440000",
            marketplace="EBAY_US",
        )
        account2 = MarketplaceAccount(
            user_uuid="550e8400-e29b-41d4-a716-446655440001",
            marketplace="EBAY_UK",
        )

        token1 = AuthToken(token="token1", ttl=3600)
        token2 = AuthToken(token="token2", ttl=3600)

        await storage.store(account1, token1)
        await storage.store(account2, token2)

        calls = mock_redis.set.call_args_list
        assert len(calls) == 2
        # Verify different keys were used
        key1 = calls[0][0][0]
        key2 = calls[1][0][0]
        assert key1 != key2
