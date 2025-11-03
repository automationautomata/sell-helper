from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from typing import Any, Dict

from pydantic import TypeAdapter

from ..domain.errors import InvalidProductData
from ..domain.item import Item, Product, TMarketplaceAspects
from ..domain.question import ProductStructure
from ..domain.value_objects import AspectData
from ..infrastructure.marketplace import (
    CategoryNotExistsError,
    MarketplaceAPI,
    MarketplaceAPIError,
)


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


class SellingServiceABC(ABC):
    @abstractmethod
    def sell_item(
        self,
        item_data: ItemData,
        marketplace_aspects_data: Dict[str, Any],
        product_data: list[AspectData],
        *images: str,
    ) -> None:
        pass


class SellingService(SellingServiceABC):
    def __init__(
        self,
        marketplace_api: MarketplaceAPI,
        marketplace_aspects_type: TMarketplaceAspects,
    ):
        self._marketplace_api = marketplace_api
        self._marketplace_aspects_type = marketplace_aspects_type

    def sell_item(
        self,
        item_data: ItemData,
        marketplace_aspects_data: Dict[str, Any],
        product_data: Dict[str, Any],
        *images: str,
    ) -> Item:
        type_adapter = TypeAdapter(self._marketplace_aspects_type)
        marketplace_aspects = type_adapter.validate_python(marketplace_aspects_data)

        product = self._validate_product_structure(item_data.category, product_data)

        item = Item(
            **asdict(item_data),
            marketplace_aspects=marketplace_aspects,
            product=product,
        )
        try:
            self._marketplace_api.publish(item, *images)

        except MarketplaceAPIError as e:
            raise SellingError() from e

    def _validate_product_structure(
        self, category_name: str, aspects_data: Dict[str, Any]
    ) -> Product:
        try:
            fields = self._marketplace_api.get_product_aspects(category_name)

        except MarketplaceAPIError as e:
            raise SellingError() from e
        except CategoryNotExistsError as e:
            raise CategoryNotFound() from e

        try:
            product_structure = ProductStructure(fields=fields)
            aspects = product_structure.validate(aspects_data).aspects
            return Product(aspects=aspects)

        except InvalidProductData as e:
            raise CategoryNotFound() from e
