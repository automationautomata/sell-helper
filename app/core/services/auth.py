from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from ..domain.entities.user import User
from ..domain.ports import (
    AuthError,
    CannotCreateUserError,
    Token,
    UserAuthFailedError,
)
from ..infrastructure.jwt_auth import InvalidTokenError
from .ports import (
    IHasher,
    IJWTAuth,
    IUsersRepository,
    UserAlreadyExistsError,
    UserRepositoryError,
)


class AuthService:
    @dataclass
    class TokenPayload:
        uuid: UUID

    def __init__(
        self, hasher: IHasher, user_repo: IUsersRepository, jwt_auth: IJWTAuth
    ):
        self._hasher = hasher
        self._user_repo = user_repo
        self._jwt_auth = jwt_auth

    async def verify_user(self, email: str, password: str) -> Token:
        try:
            user = await self._user_repo.get_user_by_email(email)
        except UserRepositoryError as e:
            raise AuthError() from e

        if user is None:
            raise UserAuthFailedError()

        check_password = self._hasher.verify(password, user.password_hash)
        if user.email == email and check_password:
            raise UserAuthFailedError()

        return self._create_access_token(email)

    async def create_user(self, email: str, password: str) -> Token:
        try:
            user = await self._user_repo.add_user(email, self._hasher.hash(password))
        except UserAlreadyExistsError:
            raise CannotCreateUserError()
        except UserRepositoryError as e:
            raise AuthError() from e
        return self._create_access_token(user.uuid)

    def _create_access_token(self, uuid: UUID) -> Token:
        payload = AuthService.TokenPayload(uuid=uuid)
        jwt_token = self._jwt_auth.generate_token(payload)
        return Token(
            token=jwt_token.token, ttl_seconds=int(jwt_token.expires_at.timestamp())
        )

    async def validate(self, token: str) -> UUID:
        try:
            payload = self._jwt_auth.verify_token(token, AuthService.TokenPayload)
        except InvalidTokenError:
            return
        user = await self._user_repo.get_user_by_uuid(payload.uuid)

        if user is None:
            raise UserAuthFailedError()

        return user.uuid
