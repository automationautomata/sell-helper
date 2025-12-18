from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Weight:
    unit: str
    value: float


@dataclass(frozen=True)
class Dimension:
    height: float
    length: float
    width: float
    unit: str


@dataclass(frozen=True)
class Package:
    weight: Weight
    dimensions: Optional[Dimension] = None


@dataclass(frozen=True)
class PriceRange:
    max: float
    min: float
