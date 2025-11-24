from dataclasses import dataclass
from typing import AsyncIterable, Dict, Type

from app.api.models.common import Marketplace
from dishka import (
    FromComponent,
    Provider,
    Scope,
    alias,
    from_context,
    provide,
)
from perplexity import Perplexity as PerplexityClient
from sqlalchemy.ext.asyncio import AsyncSession

from .api.dependencies import ISearchServicesFactory, ISellingServicesFactory
from .api.models.requests import MarketplaceAspects
from .config import EbayConfig, PerplexityConfig
from .core.domain.ebay.item import EbayMarketplaceAspects
from .core.domain.ebay.question import EbayMetadata
from .core.domain.question import Metadata
from .core.infrastructure.adapter import QuestionAdapter, QuestionAdapterABC
from .core.infrastructure.auth import JWTAuth, JWTAuthABC
from .core.infrastructure.hasher import IHasher
from .core.infrastructure.marketplace import EbayAPI, EbayClients, MarketplaceAPI
from .core.infrastructure.repository.user import UsersRepository, UsersRepositoryABC
from .core.infrastructure.search import PerplexityAndEbaySearch, SearchEngine
from .core.services.auth import AuthService, AuthServiceABC
from .core.services.search import SearchService, SearchServiceABC
from .core.services.selling import SellingService, SellingServiceABC
from .external.ebay.commerce import EbayCommerceClient
from .external.ebay.selling import EbaySellingClient
from .external.ebay.taxonomy import EbayTaxonomyClient


@dataclass
class JWTAuthSettings:
    jwt_ttl_minutes: int
    jwt_algorithm: str


class AuthServiceProvider(Provider):
    hasher = from_context(IHasher, scope=Scope.APP)
    jwt_settings = from_context(JWTAuthSettings, scope=Scope.APP)

    def __init__(self, async_session_factory: AsyncSession, scope=None, component=None):
        super().__init__(scope, component)
        self._async_session_factory = async_session_factory

    @provide(scope=Scope.APP)
    async def session(self) -> AsyncIterable[AsyncSession]:
        async with self._async_session_factory() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def jwt_auth(self, jwt_settings: JWTAuthSettings) -> JWTAuthABC:
        return JWTAuth(
            jwt_settings.jwt_ttl_minutes,
            jwt_settings.jwt_algorithm,
        )

    @provide(scope=Scope.REQUEST)
    def user_repository(self, session: AsyncSession) -> UsersRepositoryABC:
        return UsersRepository(session)

    @provide(scope=Scope.REQUEST)
    def auth_service(
        self, hasher: IHasher, user_repo: UsersRepositoryABC, jwt_auth: JWTAuthABC
    ) -> AuthServiceABC:
        return AuthService(hasher, user_repo, jwt_auth)


class EbayProvider(Provider):
    component = "ebay"
    ebay_config = from_context(EbayConfig, scope=Scope.APP)
    perplexity_config = from_context(PerplexityConfig, scope=Scope.APP)

    question_adapter = provide(
        QuestionAdapter, provides=QuestionAdapterABC, scope=Scope.APP
    )

    @provide(scope=Scope.APP)
    def metadata_type(self) -> Type[Metadata]:
        return EbayMetadata

    @provide(scope=Scope.APP)
    def marketplace_aspects_type(self) -> Type[MarketplaceAspects]:
        return EbayMarketplaceAspects

    @provide(scope=Scope.APP)
    def search(
        self, perplexity_config: PerplexityConfig, ebay_config: EbayConfig
    ) -> SearchEngine:
        perplexity_client = PerplexityClient()
        taxonomy_client = EbayTaxonomyClient(ebay_config.domain)
        return PerplexityAndEbaySearch(
            perplexity_config, perplexity_client, ebay_config, taxonomy_client
        )

    @provide(scope=Scope.APP)
    def merketplace(self, ebay_config: EbayConfig) -> MarketplaceAPI:
        clients = EbayClients(
            selling_client=EbaySellingClient(ebay_config.domain),
            taxonomy_client=EbayTaxonomyClient(ebay_config.domain),
            commerce_client=EbayCommerceClient(ebay_config.domain),
        )
        return EbayAPI(ebay_config, clients)

    @provide(scope=Scope.REQUEST)
    def search_service(
        self,
        search_engine: SearchEngine,
        marketplace_api: MarketplaceAPI,
        question_adapter: QuestionAdapterABC,
        metadata_type: Type[Metadata],
    ) -> SearchServiceABC:
        return SearchService(
            search_engine, marketplace_api, question_adapter, metadata_type
        )

    @provide(scope=Scope.REQUEST)
    def selling_service(
        self,
        marketplace_api: MarketplaceAPI,
        marketplace_aspects_type: Type[MarketplaceAspects],
    ) -> SellingServiceABC:
        return SellingService(marketplace_api, marketplace_aspects_type)


class SellingServicesFactory:
    def __init__(self, mapping: Dict[Marketplace, SellingServiceABC]):
        self._mapping = mapping

    def get(self, marketplace: str) -> SearchServiceABC:
        if marketplace not in self._mapping:
            raise ValueError(f"Invalid marketplace name {marketplace}")
        return self._mapping[marketplace]


class SearchServicesFactory:
    def __init__(self, mapping: Dict[Marketplace, SearchServiceABC]):
        self._mapping = mapping

    def get(self, marketplace: str) -> SellingServiceABC:
        if marketplace not in self._mapping:
            raise ValueError(f"Invalid marketplace name {marketplace}")
        return self._mapping[marketplace]


class ServicesFactoriesProvider(Provider):
    ebay_search = alias(
        source=SearchServiceABC, provides=SearchServiceABC, component="ebay"
    )

    ebay_selling = alias(
        SellingServiceABC, provides=SellingServiceABC, component="ebay"
    )

    @provide(scope=Scope.REQUEST)
    def selling_services_factory(
        self, ebay_selling: SellingServiceABC = FromComponent("ebay")
    ) -> ISellingServicesFactory:
        return SellingServicesFactory({Marketplace.EBAY: ebay_selling})

    @provide(scope=Scope.REQUEST)
    def search_services_factory(
        self, ebay_search: SearchServiceABC = FromComponent("ebay")
    ) -> ISearchServicesFactory:
        return SellingServicesFactory({Marketplace.EBAY: ebay_search})
