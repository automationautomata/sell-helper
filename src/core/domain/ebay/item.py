from dataclasses import dataclass
from typing import Optional

from ..item import Item, MarketplaceAspects
from .value_objects import Package


@dataclass
class EbayMarketplaceAspects(MarketplaceAspects):
    marketplace: str
    package: Package
    condition: str
    condition_description: Optional[str] = None


EbayItem = Item[EbayMarketplaceAspects]
