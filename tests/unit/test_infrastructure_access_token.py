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
    redis = AsyncMock(spec=Redis)
    redis.set = AsyncMock(return_value=None)
    redis.get = AsyncMock(return_value=None)
    redis.delete = AsyncMock(return_value=0)
    return redis


@pytest.fixture
def access_token_storage(mock_redis):
    return RedisAccessTokenStorage(redis=mock_redis)


@pytest.fixture
def test_account():
    return MarketplaceAccount(
        user_uuid="550e8400-e29b-41d4-a716-446655440000",
        marketplace="EBAY_US",
    )


@pytest.fixture
def auth_token():
    return AuthToken(token="test_token45", ttl=3600)


class TestRedisAccessTokenStorageToKey:
    def test_to_key_format(self, test_account):
        key = RedisAccessTokenStorage._to_key(test_account)

        assert isinstance(key, str)
        assert test_account.user_uuid in key
        assert test_account.marketplace in key
        assert key == f"{test_account.user_uuid}{test_account.marketplace}"

    def test_to_key_with_different_accounts(self):
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
        key1 = RedisAccessTokenStorage._to_key(test_account)
        key2 = RedisAccessTokenStorage._to_key(test_account)

        assert key1 == key2


class TestRedisAccessTokenStorageStore:
    @pytest.mark.asyncio
    async def test_store_success(
        self, access_token_storage, mock_redis, test_account, auth_token
    ):
        await access_token_storage.store(test_account, auth_token)

        expected_key = RedisAccessTokenStorage._to_key(test_account)
        mock_redis.set.assert_called_once_with(
            expected_key, auth_token.token, ex=auth_token.ttl
        )

    @pytest.mark.asyncio
    async def test_store_with_zero_ttl_raises_error(
        self, access_token_storage, test_account
    ):
        invalid_token = AuthToken(token="test_token", ttl=0)

        with pytest.raises(TokenStorageError, match="TTL must be positive"):
            await access_token_storage.store(test_account, invalid_token)

    @pytest.mark.asyncio
    async def test_store_with_negative_ttl_raises_error(
        self, access_token_storage, test_account
    ):
        invalid_token = AuthToken(token="test_token", ttl=-100)

        with pytest.raises(TokenStorageError, match="TTL must be positive"):
            await access_token_storage.store(test_account, invalid_token)

    @pytest.mark.asyncio
    async def test_store_redis_error_wrapped(
        self, access_token_storage, mock_redis, test_account, auth_token
    ):
        mock_redis.set.side_effect = RedisError("Redis connection failed")

        with pytest.raises(
            AcessTokenStorageError, match="Failed to store access token"
        ):
            await access_token_storage.store(test_account, auth_token)

    @pytest.mark.asyncio
    async def test_store_with_large_ttl(
        self, access_token_storage, mock_redis, test_account
    ):
        large_ttl_token = AuthToken(token="test_token", ttl=7776000)  # 90 days

        await access_token_storage.store(test_account, large_ttl_token)

        expected_key = RedisAccessTokenStorage._to_key(test_account)
        mock_redis.set.assert_called_once_with(expected_key, "test_token", ex=7776000)


class TestRedisAccessTokenStorageGet:
    @pytest.mark.asyncio
    async def test_get_existing_token_success(
        self, access_token_storage, mock_redis, test_account, auth_token
    ):
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
        mock_redis.get = AsyncMock(return_value=None)

        result = await access_token_storage.get(test_account)

        assert result is None
        mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_expired_token_raises_error(
        self, access_token_storage, mock_redis, test_account
    ):
        mock_redis.get = AsyncMock(return_value="expired_token")
        mock_redis.ttl = AsyncMock(return_value=-1)  # Token has expired

        with pytest.raises(TokenExpiredError):
            await access_token_storage.get(test_account)

    @pytest.mark.asyncio
    async def test_get_token_with_zero_ttl_raises_error(
        self, access_token_storage, mock_redis, test_account
    ):
        mock_redis.get = AsyncMock(return_value="token")
        mock_redis.ttl = AsyncMock(return_value=0)

        with pytest.raises(TokenExpiredError):
            await access_token_storage.get(test_account)

    @pytest.mark.asyncio
    async def test_get_redis_error_wrapped(
        self, access_token_storage, mock_redis, test_account
    ):
        mock_redis.get.side_effect = RedisError("Redis connection failed")

        with pytest.raises(AcessTokenStorageError):
            await access_token_storage.get(test_account)

    @pytest.mark.asyncio
    async def test_get_calls_correct_methods(
        self, access_token_storage, mock_redis, test_account
    ):
        mock_redis.get = AsyncMock(return_value="token")
        mock_redis.ttl = AsyncMock(return_value=3600)

        await access_token_storage.get(test_account)

        expected_key = RedisAccessTokenStorage._to_key(test_account)
        mock_redis.get.assert_called_once_with(expected_key)
        mock_redis.ttl.assert_called_once_with(expected_key)


class TestRedisAccessTokenStorageDelete:
    @pytest.mark.asyncio
    async def test_delete_success(self, access_token_storage, mock_redis, test_account):
        await access_token_storage.delete(test_account)

        expected_key = RedisAccessTokenStorage._to_key(test_account)
        mock_redis.delete.assert_called_once_with(expected_key)

    @pytest.mark.asyncio
    async def test_delete_redis_error_wrapped(
        self, access_token_storage, mock_redis, test_account
    ):
        mock_redis.delete.side_effect = RedisError("Redis connection failed")

        with pytest.raises(
            AcessTokenStorageError, match="Failed to delete access token"
        ):
            await access_token_storage.delete(test_account)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_token(
        self, access_token_storage, mock_redis, test_account
    ):
        mock_redis.delete = AsyncMock(return_value=0)  # Key didn't exist

        await access_token_storage.delete(test_account)

        mock_redis.delete.assert_called_once()


class TestRedisAccessTokenStorageIntegration:
    @pytest.mark.asyncio
    async def test_store_and_get_workflow(
        self, access_token_storage, mock_redis, test_account
    ):
        token = AuthToken(token="integration_test_token", ttl=3600)

        await access_token_storage.store(test_account, token)

        mock_redis.get = AsyncMock(return_value=token.token)
        mock_redis.ttl = AsyncMock(return_value=token.ttl)

        result = await access_token_storage.get(test_account)

        assert result.token == token.token
        assert result.ttl == token.ttl

    @pytest.mark.asyncio
    async def test_store_and_delete_workflow(
        self, access_token_storage, mock_redis, test_account
    ):
        token = AuthToken(token="integration_test_token", ttl=3600)

        await access_token_storage.store(test_account, token)
        await access_token_storage.delete(test_account)

        expected_key = RedisAccessTokenStorage._to_key(test_account)
        assert mock_redis.set.called
        assert mock_redis.delete.called
        mock_redis.delete.assert_called_with(expected_key)

    @pytest.mark.asyncio
    async def test_multiple_accounts_isolation(self, mock_redis):
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
        key1 = calls[0][0][0]
        key2 = calls[1][0][0]
        assert key1 != key2
