from dataclasses import dataclass
from typing import AsyncIterable, Dict, Type

from dishka import (
    FromComponent,
    Provider,
    Scope,
    alias,
    from_context,
    provide,
)
from perplexity import Perplexity as PerplexityClient
from shared.ebay_api.commerce import EbayCommerceClient
from shared.ebay_api.selling import EbaySellingClient
from shared.ebay_api.taxonomy import EbayTaxonomyClient
from sqlalchemy.ext.asyncio import AsyncSession

from .api.dependencies import (
    ISearchServicesFactory,
    ISellingServicesFactory,
)
from .api.models.common import Marketplace
from .config import EbayConfig
from .core.domain.entities.ebay.item import EbayMarketplaceAspects
from .core.domain.entities.ebay.question import EbayMetadata
from .core.domain.entities.item import MarketplaceAspects
from .core.domain.entities.question import Metadata
from .core.domain.ports import ISearchService, ISellingService
from .core.infrastructure.marketplace import EbayClients
from .core.infrastructure.providers import PerplexitySettings


class DBProvider(Provider):
    def __init__(self, async_session_factory: AsyncSession, scope=None, component=None):
        super().__init__(scope, component)
        self._async_session_factory = async_session_factory

    @provide(scope=Scope.APP)
    async def session(self) -> AsyncIterable[AsyncSession]:
        async with self._async_session_factory() as session:
            yield session


class PerplexityClientProvider(Provider):
    @provide(scope=Scope.APP)
    def perplexity_client(self) -> PerplexityClient:
        return PerplexityClient()

class EbayProvider(Provider):
    component = "ebay"
    ebay_config = from_context(EbayConfig, scope=Scope.APP)
    perplexity_settings = from_context(PerplexitySettings, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def ebay_clients(self, ebay_config: EbayConfig) -> EbayClients:
        return EbayClients(
            selling_client=EbaySellingClient(ebay_config.domain),
            taxonomy_client=EbayTaxonomyClient(ebay_config.domain),
            commerce_client=EbayCommerceClient(ebay_config.domain),
        )
    

    @provide(scope=Scope.APP)
    def metadata_type(self) -> Type[Metadata]:
        return EbayMetadata

    @provide(scope=Scope.APP)
    def marketplace_aspects_type(self) -> Type[MarketplaceAspects]:
        return EbayMarketplaceAspects
    
    
class SellingServicesFactory:
    def __init__(self, mapping: Dict[Marketplace, ISellingService]):
        self._mapping = mapping

    def get(self, marketplace: str) -> ISellingService:
        if marketplace not in self._mapping:
            raise ValueError(f"Invalid marketplace name {marketplace}")
        return self._mapping[marketplace]


class SearchServicesFactory:
    def __init__(self, mapping: Dict[Marketplace, ISearchService]):
        self._mapping = mapping

    def get(self, marketplace: str) -> ISearchService:
        if marketplace not in self._mapping:
            raise ValueError(f"Invalid marketplace name {marketplace}")
        return self._mapping[marketplace]


class ServicesFactoriesProvider(Provider):
    ebay_search = alias(ISearchService, provides=ISearchService, component="ebay")

    ebay_selling = alias(ISellingService, provides=ISellingService, component="ebay")

    @provide(scope=Scope.REQUEST)
    def selling_services_factory(
        self, ebay_selling: ISellingService = FromComponent("ebay")
    ) -> ISellingServicesFactory:
        return SellingServicesFactory({Marketplace.EBAY: ebay_selling})

    @provide(scope=Scope.REQUEST)
    def search_services_factory(
        self, ebay_search: ISearchService = FromComponent("ebay")
    ) -> ISearchServicesFactory:
        return SearchServicesFactory({Marketplace.EBAY: ebay_search})
