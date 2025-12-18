from dataclasses import dataclass

from ..question import Metadata
from .value_objects import Package, PriceRange


@dataclass
class EbayMetadata(Metadata):
    package: Package
    price_range: PriceRange
    currency: str
