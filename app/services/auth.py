from dataclasses import dataclass
from uuid import UUID

from ..domain.dto import Token
from ..domain.ports import (
    AuthError,
    CannotCreateUser,
    InvalidUserToken,
)
from .ports import (
    IHasher,
    IJWTAuth,
    IUserRepository,
    UserAlreadyExists,
    UserRepositoryError,
)


@dataclass
class TokenPayload:
    uuid: UUID


@dataclass
class AuthService:
    hasher: IHasher
    user_repo: IUserRepository
    jwt_auth: IJWTAuth[TokenPayload]

    async def verify_user(self, email: str, password: str) -> Token:
        try:
            user = await self.user_repo.get_user_by_email(email)
        except UserRepositoryError as e:
            raise AuthError() from e

        if user is None:
            raise InvalidUserToken()

        check_password = self.hasher.verify(password, user.password_hash)
        if not (user.email == email and check_password):
            raise InvalidUserToken()

        return self._create_access_token(email)

    async def add_user(self, email: str, password: str) -> Token:
        try:
            user = await self.user_repo.add_user(email, self.hasher.hash(password))
            return self._create_access_token(user.uuid)

        except UserAlreadyExists as e:
            raise CannotCreateUser() from e
        except UserRepositoryError as e:
            raise AuthError() from e

    def _create_access_token(self, uuid: UUID) -> Token:
        payload = TokenPayload(uuid=uuid)
        jwt_token = self.jwt_auth.generate_token(payload)
        return Token(token=jwt_token.token, ttl_seconds=jwt_token.ttl)

    async def validate(self, token: str) -> UUID:
        payload = self.jwt_auth.verify_token(token, TokenPayload)
        if payload is None:
            raise InvalidUserToken()

        try:
            user = await self.user_repo.get_user_by_uuid(payload.uuid)
        except UserRepositoryError as e:
            raise AuthError() from e

        if user is None:
            raise InvalidUserToken()

        return user.uuid
