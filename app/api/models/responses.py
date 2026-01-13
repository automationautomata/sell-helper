from typing import Any, Dict, List

from pydantic import BaseModel

from .common import Package


class ErrorResponse(BaseModel):
    error: str


class TokenResponse(BaseModel):
    token: str
    ttl: int


class SearchCategoriesResponse(BaseModel):
    product_name: str
    categories: List[str]


class Aspects(BaseModel):
    values: Dict[str, Any]
    required: List[str]


class Metadata(BaseModel):
    description: str


class EbayMetadata(Metadata):
    package: Package
    currency: str


MetadataUnion = EbayMetadata | Metadata


class SearchAspectsResponse(BaseModel):
    metadata: MetadataUnion
    aspects: Aspects


class PublishItemResponse(BaseModel):
    status: str


class MarketplaceLogoutResponse(BaseModel):
    status: str
