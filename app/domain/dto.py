import uuid
from dataclasses import dataclass
from typing import Any


@dataclass
class Token:
    token: str
    ttl_seconds: int


@dataclass()
class AspectValueDTO:
    name: str
    value: Any
    is_required: bool


@dataclass
class ProductDTO:
    metadata: dict[str]
    aspects: list[AspectValueDTO]


@dataclass()
class ProductCategoriesDTO:
    product_name: str
    categories: list[str]


@dataclass
class ItemDTO:
    title: str
    description: str
    price: float
    currency: str
    country: str
    quantity: int
    category: str
    marketplace_aspects_data: dict[str]
    product_aspects: dict[str]


@dataclass
class MarketplaceAccountDTO:
    user_uuid: uuid.UUID
    marketplace: str
