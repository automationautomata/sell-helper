from dataclasses import asdict
from typing import Any, Dict, Union

from pydantic import BaseModel

from ...core.domain.ebay.value_objects import PriceRange
from ...core.domain.item import Item
from ...core.domain.question import Answer
from .common import Package


class ErrorResponse(BaseModel):
    error: str


class TokenResponse(BaseModel):
    token: str
    ttl: int


class ProductCategoriesResponse(BaseModel):
    product_name: str
    categories: list[str]


class Product(BaseModel):
    aspects: Dict[str, Any]
    required: list[str]


class MetadataResponse(BaseModel):
    description: str


class EbayMetadataResponse(MetadataResponse):
    package: Package
    currency: str
    price_range: PriceRange


MetadataUnion = Union[EbayMetadataResponse, MetadataResponse]


class ProductResponse(BaseModel):
    metadata_type: str
    metadata: MetadataUnion
    product: Product

    @classmethod
    def from_domain(cls, answer: Answer) -> "ProductResponse":
        metadata_type_name = type(answer.metadata).__name__

        aspects = {}
        required = []
        for aspect_data in answer.product_data.aspects:
            name, value = aspect_data.name, aspect_data.value

            aspects[name] = value
            if aspect_data.is_required:
                required.append(name)

        return cls.model_validate(
            dict(
                metadata_type=metadata_type_name,
                metadata=asdict(answer.metadata),
                product=dict(aspects=aspects, required=required),
            )
        )


class ItemResponse(BaseModel):
    title: str
    description: str
    price: float
    currency: str
    country: str
    quantity: int
    product_details: Dict[str, Any]
    marketplace_details: Dict[str, Any]
    marketplace_name: str

    @classmethod
    def from_domain(cls, marketplace_name: str, item: Item) -> "ItemResponse":
        marketplace_details = asdict(item.marketplace_aspects)
        product_details = asdict(item.product)

        return cls(
            title=item.title,
            description=item.description,
            price=item.price,
            currency=item.currency,
            country=item.country,
            quantity=item.quantity,
            product_details=product_details,
            marketplace_details=marketplace_details,
            marketplace_name=marketplace_name,
        )
