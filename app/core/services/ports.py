import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional, Protocol, Type

from ..domain.entities.item import Item
from ..domain.entities.user import User
from ..domain.entities.value_objects import AspectField


class SearchEngineError(Exception):
    pass


class CategoriesNotFoundError(SearchEngineError):
    pass


class ISearchEngine(Protocol):
    def by_product_name(
        self, product_name: str, comment: str, json_schema: dict[str, Any]
    ) -> dict:
        """raise SearchEngineError"""
        pass

    def by_barecode(self, barecode: str) -> str:
        """Search product name by barecode.

        raise SearchEngineError
        """
        pass

    def barecodes_on_image(self, img_path: str) -> list[str]:
        """raise SearchEngineError"""
        pass

    def categories(self, product_name: str) -> list[str]:
        """raise CategoriesNotFoundError or SearchEngineError"""
        pass


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


class IJWTAuth[T](Protocol):
    def generate_token(self, data: T) -> JWTToken:
        pass

    def verify_token(self, token: str, payload_data_type: Type[T]) -> Any:
        pass


class IHasher(Protocol):
    def verify(plain: str, hash: str) -> bool:
        pass

    def hash(data: str) -> str:
        pass


class MarketplaceAPIError(Exception):
    pass


class CategoryNotExistsError(MarketplaceAPIError):
    pass


class InvalidValue(MarketplaceAPIError):
    pass


class IMarketplaceAPI(Protocol):
    def publish(self, product: Item, *images: str) -> None:
        pass

    def get_category_id(self, category_name: str) -> str:
        pass

    def get_product_aspects(self, category_name: str) -> list[AspectField]:
        pass


class UserRepositoryError(Exception):
    pass


class UserAlreadyExistsError(UserRepositoryError):
    pass


class IUsersRepository(Protocol):
    async def get_user_by_uuid(self, uuid: uuid.UUID) -> Optional[User]:
        pass

    async def get_user_by_email(self, email: str) -> Optional[User]:
        pass

    async def add_user(self, email: str, password_hash: str) -> User:
        pass


class MarketplaceOAuthError(Exception):
    pass


@dataclass
class MarketplaceTokens:
    access_token: str
    refresh_token: str
    refresh_token_ttl: int
    access_token_ttl: int


class IMarketplaceOAuth(Protocol):
    def get_tokens(self, code: str) -> MarketplaceTokens:
        pass

    def generate_auth_url(self, state: str) -> str:
        pass


class AccessTokensStorageError(Exception):
    pass


@dataclass
class Token:
    token: str
    ttl: int


class IAccessTokensStorage(Protocol):
    async def store(self, key: str, token: Token) -> None:
        pass

    async def get(self, key: str) -> Token:
        pass


class RefreshTokensStorageError(Exception):
    pass


class IRefreshTokensStorage(Protocol):
    async def store(self, uuid: uuid.UUID, token: Token) -> None:
        pass

    async def remove(self, uuid: uuid.UUID) -> Token:
        pass
