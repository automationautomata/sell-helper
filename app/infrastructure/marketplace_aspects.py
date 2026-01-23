from dataclasses import asdict, dataclass
from typing import Self

from pydantic import TypeAdapter

from .metadata import EbayPackage


@dataclass
class EbayPolicies:
    fulfillment_policy: str
    payment_policy: str
    return_policy: str


@dataclass
class EbayAspects:
    location: str
    marketplace: str
    policies: EbayPolicies
    package: EbayPackage
    condition: str
    condition_description: str | None = None

    @classmethod
    def validate(cls, data: dict[str]) -> Self | None:
        return TypeAdapter(cls).validate_python(data)

    def asdict(self) -> dict[str]:
        return asdict(self)
