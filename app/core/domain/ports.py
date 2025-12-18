from dataclasses import dataclass
from typing import Any, Optional, Protocol

from .entities.question import Answer
from .entities.user import User
from .entities.value_objects import AspectData


class AuthError(Exception):
    pass


@dataclass
class Token:
    token: str
    ttl_seconds: int


class IAuthService(Protocol):
    async def verify_user(self, email: str, password: str) -> bool:
        pass

    def create_access_token(self, email: str) -> Token:
        pass

    async def validate(token: str) -> Optional[User]:
        pass


class SearchError(Exception):
    pass


class ProductCategoriesNotFoundError(SearchError):
    pass


@dataclass(frozen=True)
class ProductCategories:
    product_name: str
    categories: list[str]


class ISearchService(Protocol):
    DEAFULT_QUESTION = "Provide information by the image"

    def product(self, product_name: str, category: str, comment: str) -> Answer:
        """Search product by name and category"""
        pass

    def product_categories(self, img_path: str) -> ProductCategories:
        """Search categories by product name"""
        pass


class SellingError(Exception):
    pass


class CategoryNotFound(SellingError):
    pass


@dataclass
class ItemData:
    title: str
    description: str
    price: float
    currency: str
    country: str
    quantity: int
    category: str


class ISellingService(Protocol):
    def sell_item(
        self,
        item_data: ItemData,
        marketplace_aspects_data: dict[str, Any],
        product_data: list[AspectData],
        *images: str,
    ) -> None:
        pass
