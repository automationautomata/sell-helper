import uuid
from dataclasses import dataclass
from typing import Protocol

from ...domain.entities import (
    AspectField,
    IMetadata,
    Item,
    MarketplaceAccount,
    Product,
    ProductStructure,
    User,
)


class ISearchEngine(Protocol):
    def by_product_name(
        self,
        metadata_type: type[IMetadata],
        product_structure: ProductStructure,
        comment: str,
    ) -> Product:
        """raise SearchEngineError"""
        pass

    def product_name_by_barecode(self, barecode: str) -> str:
        """Search product name by barecode.

        raise SearchEngineError
        """
        pass

    def barecodes_on_image(self, img_path: str) -> list[str]:
        """raise SearchEngineError"""
        pass


@dataclass
class AuthToken:
    token: str
    ttl: int


class IJWTAuth[T](Protocol):
    def generate_token(self, payload: T) -> AuthToken:
        pass

    def verify_token(self, token: str, data_type: type[T]) -> T:
        pass


class IHasher(Protocol):
    def verify(plain: str, hash: str) -> bool:
        pass

    def hash(data: str) -> str:
        pass


class IMarketplaceAPI(Protocol):
    def publish(self, product: Item, token: str, *images: str) -> None:
        pass

    def get_product_aspects(
        self, category_name: str, **marketplace_settings: dict
    ) -> list[AspectField]:
        pass


class ICategoryPredictor(Protocol):
    def predict(self, product_name: str, **marketplace_settings: dict) -> list[str]:
        pass


class IUserRepository(Protocol):
    async def get_user_by_uuid(self, uuid: uuid.UUID) -> User | None:
        pass

    async def get_user_by_email(self, email: str) -> User | None:
        pass

    async def add_user(self, email: str, password_hash: str) -> User:
        pass


class ITokenStorage(Protocol):
    async def store(self, account: MarketplaceAccount, token: AuthToken):
        pass

    async def get(self, account: MarketplaceAccount) -> AuthToken | None:
        pass

    async def delete(self, account: MarketplaceAccount):
        pass


IAccessTokenStorage = ITokenStorage


IRefreshTokenStorage = ITokenStorage


@dataclass
class OAuth2Tokens:
    access_token: AuthToken
    refresh_token: AuthToken


class IMarketplaceOAuth(Protocol):
    async def new_access_token(self, refresh_token: str) -> AuthToken:
        pass

    def parse(self, data: dict[str]) -> OAuth2Tokens:
        pass
