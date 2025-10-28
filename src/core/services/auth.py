from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from ..domain.user import User
from ..infrastructure.auth import InvalidTokenError, JWTAuthABC
from ..infrastructure.hasher import IHasher
from ..infrastructure.repository.user import UsersRepositoryABC


class AuthError(Exception):
    pass


@dataclass
class Token:
    token: str
    ttl_seconds: int


class AuthServiceABC(ABC):
    @abstractmethod
    def verify_user(self, email: str, password: str) -> bool:
        pass

    @abstractmethod
    def create_access_token(self, email: str) -> Token:
        pass

    @abstractmethod
    def validate(token: str) -> Optional[User]:
        pass


class AuthService(AuthServiceABC):
    @dataclass
    class TokenPayload:
        email: str

    def __init__(
        self, hasher: IHasher, user_repo: UsersRepositoryABC, jwt_auth: JWTAuthABC
    ):
        self._hasher = hasher
        self._user_repo = user_repo
        self._jwt_auth = jwt_auth

    def verify_user(self, email: str, password: str) -> bool:
        user = self._user_repo.get_user_by_email(email)
        if user is None:
            return False

        check_password = self._hasher.verify(
            user.password_hash, f"{password}{user.salt}"
        )
        return user.email == email and check_password

    def create_access_token(self, email: str) -> Token:
        payload = AuthService.TokenPayload(email=email)
        jwt_token = self._jwt_auth.generate_token(payload)
        return Token(token=jwt_token.token, ttl_seconds=jwt_token.expires_at.second)

    def validate(self, token: str) -> Optional[User]:
        try:
            payload = self._jwt_auth.verify_token(token, AuthService.TokenPayload)
        except InvalidTokenError:
            return

        return self._user_repo.get_user_by_email(payload.email)
