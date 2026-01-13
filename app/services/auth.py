from dataclasses import dataclass
from uuid import UUID

from ..domain.dto import Token
from ..domain.ports import (
    AuthError,
    CannotCreateUserError,
    UserAuthFailedError,
)
from ..infrastructure.jwt_auth import InvalidTokenError
from .ports import (
    IHasher,
    IJWTAuth,
    IUserRepository,
    UserAlreadyExistsError,
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
            raise UserAuthFailedError()

        check_password = self.hasher.verify(password, user.password_hash)
        if user.email == email and check_password:
            raise UserAuthFailedError()

        return self._create_access_token(email)

    async def add_user(self, email: str, password: str) -> Token:
        try:
            user = await self.user_repo.add_user(email, self.hasher.hash(password))
            return self._create_access_token(user.uuid)

        except UserAlreadyExistsError:
            raise CannotCreateUserError()
        except UserRepositoryError as e:
            raise AuthError() from e

    def _create_access_token(self, uuid: UUID) -> Token:
        payload = TokenPayload(uuid=uuid)
        jwt_token = self.jwt_auth.generate_token(payload)
        return Token(
            token=jwt_token.token, ttl_seconds=int(jwt_token.expires_at.timestamp())
        )

    async def validate(self, token: str) -> UUID:
        try:
            payload = self.jwt_auth.verify_token(token, TokenPayload)
        except InvalidTokenError:
            return
        user = await self.user_repo.get_user_by_uuid(payload.uuid)

        if user is None:
            raise UserAuthFailedError()

        return user.uuid
