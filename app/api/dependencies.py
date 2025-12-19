from typing import Protocol

from ..core.domain.ports import IMarketplaceAuthService, ISearchService, ISellingService
from .models.common import Marketplace


class ISearchServicesFactory(Protocol):
    def get(self, marketplace: Marketplace) -> ISearchService:
        pass


class ISellingServicesFactory(Protocol):
    def get(self, marketplace: Marketplace) -> ISellingService:
        pass


class IMarketplaceAuthServicesFactory(Protocol):
    def get(self, marketplace: Marketplace) -> IMarketplaceAuthService:
        pass
