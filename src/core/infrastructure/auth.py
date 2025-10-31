import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Type

import jwt
from data import EnvKeys
from pydantic import TypeAdapter, ValidationError


class JWTAuthError(Exception):
    pass


class InvalidTokenError(JWTAuthError):
    pass


class InvalidPayloadTypeError(JWTAuthError):
    pass


@dataclass
class JWTToken:
    token: str
    expires_at: datetime


class JWTAuthABC(ABC):
    @abstractmethod
    def generate_token(self, data: Any) -> JWTToken:
        pass

    @abstractmethod
    def verify_token(self, token: str, payload_data_type: Type) -> Any:
        pass


class JWTAuth(JWTAuthABC):
    def __init__(self, jwt_ttl_minutes: int, jwt_algorithm: str):
        self._jwt_ttl_minutes = jwt_ttl_minutes
        self._jwt_algorithm = jwt_algorithm

    def generate_token(self, data: Any) -> JWTToken:
        delta = timedelta(minutes=self._jwt_ttl_minutes)
        expires_at = datetime.now(timezone.utc) + delta

        payload = {"exp": expires_at, "data": TypeAdapter(type(data)).dump_python(data)}
        token = jwt.encode(
            payload, os.getenv(EnvKeys.JWT_SECRET), algorithm=self._jwt_algorithm
        )
        return JWTToken(token=token, expires_at=expires_at)

    def verify_token(self, token: str, data_type: Type) -> Any:
        try:
            payload = jwt.decode(
                token,
                os.getenv(EnvKeys.JWT_SECRET),
                algorithms=[self._jwt_algorithm],
            )
            return TypeAdapter(data_type).validate_python(payload["data"])

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
            raise InvalidTokenError() from e

        except ValidationError as e:
            raise InvalidPayloadTypeError() from e
