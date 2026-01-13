from dataclasses import dataclass
from typing import final

from .common import AspectValue, Validatable


class IMarketplaceAspects(Validatable):
    pass


@final
@dataclass
class Item[T: IMarketplaceAspects]:
    title: str
    description: str
    price: float
    currency: str
    country: str
    quantity: int
    category: str
    product_aspects: list[AspectValue]
    marketplace_aspects: IMarketplaceAspects
