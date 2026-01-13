from dataclasses import dataclass

from redis.asyncio import Redis, RedisError

from ..domain.entities import MarketplaceAccount
from ..services.ports import (
    AcessTokenStorageError,
    AuthToken,
    TokenExpiredError,
    TokenStorageError,
)


@dataclass
class RedisAccessTokenStorage:
    redis: Redis

    @staticmethod
    def _to_key(account: MarketplaceAccount):
        return f"{account.user_uuid}{account.marketplace}"

    async def store(self, account: MarketplaceAccount, token: AuthToken):
        if token.ttl <= 0:
            raise TokenStorageError("TTL must be positive")

        try:
            await self.redis.set(self._to_key(account), token.token, ex=token.ttl)
        except RedisError as exc:
            raise AcessTokenStorageError("Failed to store access token") from exc

    async def get(self, account: MarketplaceAccount) -> AuthToken | None:
        key = self._to_key(account)
        try:
            value = await self.redis.get(key)
        except RedisError as e:
            raise AcessTokenStorageError() from e

        if value is None:
            return

        ttl = await self.redis.ttl(key)
        if ttl <= 0:
            raise TokenExpiredError()

        return AuthToken(token=value, ttl=ttl)

    async def delete(self, account: MarketplaceAccount):
        try:
            await self.redis.delete(self._to_key(account))
        except RedisError as exc:
            raise AcessTokenStorageError("Failed to delete access token") from exc
