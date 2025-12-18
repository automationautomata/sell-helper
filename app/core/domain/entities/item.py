from dataclasses import dataclass
from typing import Generic, TypeVar, final

from .value_objects import AspectData


@dataclass
class Product:
    aspects: list[AspectData]


@dataclass
class MarketplaceAspects:
    pass


TMarketplaceAspects = TypeVar("TMarketplaceAspects", bound=MarketplaceAspects)


@final
@dataclass
class Item(Generic[TMarketplaceAspects]):
    title: str
    description: str
    price: float
    currency: str
    country: str
    quantity: int
    category: str
    product: Product
    marketplace_aspects: TMarketplaceAspects
