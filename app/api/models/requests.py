import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, model_validator

from .common import Package


class UserLogin(BaseModel):
    email: str
    password: str


class UserRegistration(BaseModel):
    email: str
    password: str


class EbayOptions(BaseModel):
    marketplace: str


class SearchOptions(BaseModel):
    options: EbayOptions | None


class SearchProductAspects(BaseModel):
    product_name: str
    category: str
    comment: str = ""
    options: SearchOptions


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


class EbayAspects(MarketplaceAspects):
    class Policies(BaseModel):
        fulfillment_policy_id: str
        payment_policy_id: str
        return_policy_id: str

    location_key: str
    marketplace: str
    package: Package
    condition: EbayCondition
    policies: Policies
    condition: str
    condition_description: str | None = None


MarketplaceAspectsUnion = EbayAspects | MarketplaceAspects


class PublishItem(BaseModel):
    title: str
    description: str
    price: float
    currency: str
    country: str
    quantity: int
    category: str
    product_aspects: dict[str, Any]
    marketplace_aspects_data: MarketplaceAspectsUnion

    @model_validator(mode="before")
    @classmethod
    def validator(cls, value):
        if isinstance(value, str | bytes | bytearray):
            return json.loads(value)
        return value
