from dataclasses import asdict, dataclass
from typing import Self

from pydantic import TypeAdapter


@dataclass
class Weight:
    unit: str
    value: float


@dataclass
class Dimension:
    height: float
    length: float
    width: float
    unit: str


@dataclass
class EbayPackage:
    weight: Weight
    dimensions: Dimension | None = None


@dataclass
class EbayMetadata:
    description: str
    package: EbayPackage

    @classmethod
    def validate(cls, data: dict[str]) -> Self | None:
        return TypeAdapter(cls).validate_python(data)

    def asdict(self) -> dict[str]:
        return asdict(self)
