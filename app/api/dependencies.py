from typing import Protocol

from ..core.services.price_statistics import PriceStatisticsServiceABC
from ..core.services.search import SearchServiceABC
from ..core.services.selling import SellingServiceABC
from .models.common import Marketplace


class ISearchServicesFactory(Protocol):
    def get(self, marketplace: Marketplace) -> SearchServiceABC:
        pass


class ISellingServicesFactory(Protocol):
    def get(self, marketplace: Marketplace) -> SellingServiceABC:
        pass


class IPriceStatisticsServicesFactory(Protocol):
    def get(self, marketplace: Marketplace) -> PriceStatisticsServiceABC:
        pass
