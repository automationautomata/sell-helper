from typing import Protocol

from ..core.domain.ports import ISearchService, ISellingService
from .models.common import Marketplace


class ISearchServicesFactory(Protocol):
    def get(self, marketplace: Marketplace) -> ISearchService:
        pass


class ISellingServicesFactory(Protocol):
    def get(self, marketplace: Marketplace) -> ISellingService:
        pass
