import json
from enum import Enum
from typing import Any, Dict, Optional, Union

from pydantic import BaseModel, model_validator

from .common import Package


class UserSingInRequest(BaseModel):
    email: str
    password: str


class ProductRequest(BaseModel):
    product_name: str
    category: str
    comment: str = ""


class MarketplaceAspects(BaseModel):
    pass


class EbayCondition(str, Enum):
    NEW = "NEW"
    LIKE_NEW = "LIKE_NEW"
    NEW_OTHER = "NEW_OTHER"
    USED_EXCELLENT = "USED_EXCELLENT"
    USED_GOOD = "USED_GOOD"
    USED_ACCEPTABLE = "USED_ACCEPTABLE"
    FOR_PARTS_OR_NOT_WORKING = "FOR_PARTS_OR_NOT_WORKING"


class EbayMarketplaceAspects(MarketplaceAspects):
    marketplace: str
    package: Package
    condition: EbayCondition
    condition_description: Optional[str] = None


MarketplaceAspectsUnion = Union[EbayMarketplaceAspects, MarketplaceAspects]


class SellItemRequest(BaseModel):
    title: str
    description: str
    price: float
    currency: str
    country: str
    quantity: int
    category: str
    product: Dict[str, Any]
    marketplace_aspects: MarketplaceAspectsUnion

    @model_validator(mode="before")
    @classmethod
    def validator(cls, value):
        if isinstance(value, (str, bytes, bytearray)):
            return json.loads(value)
        return value
