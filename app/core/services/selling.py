from dataclasses import asdict
from typing import Any, Dict

from pydantic import TypeAdapter

from ..domain.entities.errors import InvalidProductData
from ..domain.entities.item import Item, Product, TMarketplaceAspects
from ..domain.entities.question import ProductStructure
from ..domain.ports import CategoryNotFound, ItemData, SellingError
from .ports import (
    CategoryNotExistsError,
    IMarketplaceAPI,
    MarketplaceAPIError,
)


class SellingService:
    def __init__(
        self,
        marketplace_api: IMarketplaceAPI,
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

        except CategoryNotExistsError as e:
            raise CategoryNotFound() from e
        except MarketplaceAPIError as e:
            raise SellingError() from e

        try:
            product_structure = ProductStructure(fields=fields)
            aspects = product_structure.validate(aspects_data).aspects
            return Product(aspects=aspects)

        except InvalidProductData as e:
            raise CategoryNotFound() from e
