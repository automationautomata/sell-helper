from dataclasses import asdict
from typing import Any, Dict, Union

from core.domain.ebay.question import EbayMetadata
from core.domain.item import Item
from core.domain.question import Answer, Metadata
from pydantic import BaseModel


class ErrorResponse(BaseModel):
    error: str


class ProductCategoriesResponse(BaseModel):
    product_name: str
    categories: list[str]


class Product(BaseModel):
    aspects: Dict[str, Any]
    required: list[str]


MetadataUnion = Union[EbayMetadata, Metadata]


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

        return cls(
            metadata_type=metadata_type_name,
            metadata=asdict(answer.metadata),
            product=Product(aspects=aspects, required=required),
        )


ItemUnion = Union[EbayMetadata, Metadata]


class ItemResponse(BaseModel):
    title: str
    description: str
    condition: str
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
            condition=item.condition,
            price=item.price,
            currency=item.currency,
            country=item.country,
            quantity=item.quantity,
            product_details=product_details,
            marketplace_details=marketplace_details,
            marketplace_name=marketplace_name,
        )
