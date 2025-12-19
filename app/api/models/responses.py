from dataclasses import asdict
from typing import Any, Dict, Union

from pydantic import BaseModel

from ...core.domain.entities.ebay.value_objects import PriceRange
from ...core.domain.entities.question import Answer
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


class PublishItemResponse(BaseModel):
    status: str


class AuthURLResponse(BaseModel):
    auth_url: str
