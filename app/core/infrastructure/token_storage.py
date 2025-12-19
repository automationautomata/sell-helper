import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict

import aiohttp
import redis.asyncio as redis

from ..services.ports import TokenStorageError


@dataclass
class RedisTokenStorageConfig:
    redis_url: str
    token_refresh_url: str
    client_id: str
    client_secret: str
    access_ttl: int
    refresh_ttl: int


class RedisTokenStorage:
    def __init__(self, redis: redis.Redis, config: RedisTokenStorageConfig):
        self._redis = redis
        self._refresh_url = config.token_refresh_url
        self._client_id = config.client_id
        self._client_secret = config.client_secret
        self._access_ttl = config.access_ttl
        self._refresh_ttl = config.refresh_ttl
        
    async def store_tokens(
        self, key: str, access_token: str, refresh_token: str, ttl: int
    ) -> None:
        pass

    async def get_tokens(self, key: str) -> Optional[tuple[str, str]]:
        pass

    async def get_token(self, user_id: str, service: str = "default") -> Dict[str, Any]:
        """Получить access token, обновив при необходимости"""
        key = f"token:{service}:{user_id}"

        token_data = await self._redis.get(key)
        if token_data:
            token_info = json.loads(token_data)
            if self._is_valid_token(token_info):
                return token_info

        new_token = await self._refresh_token(user_id)
        await self._store_token(key, new_token)
        return new_token

    async def store_refresh_token(self, user_id: str, refresh_token: str):
        refresh_key = f"refresh:{user_id}"
        await self._redis.setex(refresh_key, self._refresh_ttl, refresh_token)

    def _is_valid_token(self, token_info: Dict[str, Any]) -> bool:
        expires_at = datetime.fromisoformat(token_info["expires_at"])
        return datetime.now() < expires_at - timedelta(seconds=30) 

    async def _store_token(self, key: str, token_data: Dict[str, Any]):
        await self._redis.setex(key, self._access_ttl, json.dumps(token_data))

    async def close(self):
        await self._redis.close()
