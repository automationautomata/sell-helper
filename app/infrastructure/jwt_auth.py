from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import jwt
from pydantic import TypeAdapter, ValidationError

from ..services.ports import AuthToken, InvalidPayloadTypeError, InvalidTokenError


@dataclass
class JWTAuth[T]:
    jwt_ttl_minutes: int
    jwt_algorithm: str
    jwt_secret: str

    def generate_token(self, data: T) -> AuthToken:
        delta = timedelta(minutes=self.jwt_ttl_minutes)

        now = datetime.now(timezone.utc)
        expires_at = now + delta
        payload = {
            "iat": now,
            "exp": expires_at,
            "data": TypeAdapter(type(data)).dump_python(data),
        }

        token = jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
        return AuthToken(token=token, expires_at=delta.total_seconds())

    def verify_token(self, token: str, data_type: type[T]) -> T:
        try:
            payload = jwt.decode(
                token, self.jwt_secret, algorithms=[self.jwt_algorithm]
            )
            return TypeAdapter(data_type).validate_python(payload["data"])

        except (jwt.ExpiredSignatureError, jwt.InvalidTokenError) as e:
            raise InvalidTokenError() from e

        except ValidationError as e:
            raise InvalidPayloadTypeError() from e
