from dataclasses import dataclass
from typing import final

from .common import AspectValue, Validatable


class IMetadata(Validatable):
    pass


@final
@dataclass
class Product[M: IMetadata]:
    metadata: M
    aspects: list[AspectValue]
