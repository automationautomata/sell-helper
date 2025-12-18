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


class IUsersRepository(Protocol):
    async def get_user_by_email(self, email: str) -> Optional[User]:
        pass
