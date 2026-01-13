from collections.abc import Generator
from dataclasses import asdict, dataclass
from typing import Annotated

from dishka import (
    FromComponent,
    Provider,
    Scope,
    from_context,
    provide,
)
from perplexity import Perplexity as PerplexityClient

from ..data import Marketplace, OAuth2Settings
from ..domain.entities import IMarketplaceAspects, IMetadata
from ..services import ports
from .access_token_storage import RedisAccessTokenStorage
from .api_clients import ebay as ebay_api
from .category_predictor import EbayCategoryPredictor
from .factory import InfraFactory
from .jwt_auth import JWTAuth
from .marketplace_api import EbayAPI
from .marketplace_aspects import EbayAspects
from .metadata import EbayMetadata
from .oauth import EbayOAuth
from .search import SearchEngine


@dataclass
class JWTAuthSettings:
    jwt_ttl_minutes: int
    jwt_algorithm: str
    jwt_secret: str


@dataclass
class SearchEngineSettings:
    perplexity_model: str
    barcode_search_token: str


class InfrastructureProvider(Provider):
    jwt_settings = from_context(JWTAuthSettings, scope=Scope.APP)

    perplexity_settings = from_context(SearchEngineSettings, scope=Scope.APP)
    access_tokens_storage = provide(
        RedisAccessTokenStorage, provides=ports.IAccessTokenStorage, scope=Scope.REQUEST
    )

    @provide(scope=Scope.REQUEST)
    def jwt_auth(self, jwt_settings: JWTAuthSettings) -> ports.IJWTAuth:
        return JWTAuth(**asdict(jwt_settings))

    @provide(scope=Scope.REQUEST)
    def search(
        self, settings: SearchEngineSettings, client: PerplexityClient
    ) -> ports.ISearchEngine:
        return SearchEngine(client, **asdict(settings))


OAuthStateAuthSettings = JWTAuthSettings


class OAuthStateAuthProvider(Provider):
    component = "oauth_state_auth"

    jwt_settings = from_context(OAuthStateAuthSettings, scope=Scope.APP)

    @provide(scope=Scope.REQUEST)
    def jwt_auth(self, jwt_settings: OAuthStateAuthSettings) -> ports.IJWTAuth:
        return JWTAuth(**asdict(jwt_settings))


@dataclass
class EbayClientSettings:
    domain: str
    oauth_settings: OAuth2Settings


@dataclass
class EbayClients:
    selling_api: ebay_api.EbaySellingClient
    taxonomy_api: ebay_api.EbayTaxonomyClient
    commerce_api: ebay_api.EbayCommerceClient
    user_client: ebay_api.EbayUserClient


SKUGenerator = Generator[str, None, None]


class EbayInfrastructureProvider(Provider):
    component = "ebay"

    @provide(scope=Scope.REQUEST)
    def ebay_clients(self, settings: EbayClientSettings) -> EbayClients:
        return EbayClients(
            ebay_api.EbayTaxonomyClient(settings.domain, settings.oauth_settings),
            ebay_api.EbaySellingClient(settings.domain, settings.oauth_settings),
            ebay_api.EbayCommerceClient(settings.domain, settings.oauth_settings),
            ebay_api.EbayUserClient(settings.domain, settings.oauth_settings),
        )

    @provide(scope=Scope.REQUEST)
    def merketplace_api(self, clients: EbayClients, sku_gen: SKUGenerator) -> EbayAPI:
        return EbayAPI(
            clients.taxonomy_api, clients.commerce_api, clients.selling_api, sku_gen
        )

    @provide(scope=Scope.REQUEST)
    def category_predictor(self, clients: EbayClients) -> EbayCategoryPredictor:
        return EbayCategoryPredictor(taxonomy_api=clients.taxonomy_api)

    @provide(scope=Scope.REQUEST)
    def ebay_oauth(self, clients: EbayClients) -> EbayOAuth:
        return EbayOAuth(client=clients.user_client)


class FactoriesProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def merketplace_api_factory(
        self, ebay_api: Annotated[EbayAPI, FromComponent("ebay")]
    ) -> ports.IMarketplaceAPIFactory:
        return InfraFactory[ports.IMarketplaceAPI]({Marketplace.EBAY: ebay_api})

    @provide(scope=Scope.REQUEST)
    def category_predictors_factory(
        self, ebay_predictor: Annotated[EbayCategoryPredictor, FromComponent("ebay")]
    ) -> ports.ICategoryPredictorFactory:
        return InfraFactory[ports.ICategoryPredictor](
            {Marketplace.EBAY: ebay_predictor}
        )

    @provide(scope=Scope.REQUEST)
    def marketplace_oauth_factory(self) -> ports.IMarketplaceOAuthFactory:
        return InfraFactory[ports.IMarketplaceOAuth]({Marketplace.EBAY: EbayOAuth})

    @provide(scope=Scope.REQUEST)
    def metadata_factory(self) -> ports.IMetadataFactory:
        return InfraFactory[IMetadata]({Marketplace.EBAY: EbayMetadata})

    @provide(scope=Scope.REQUEST)
    def marketplace_aspects_factory(self) -> ports.IMarketplaceAspectsFactory:
        return InfraFactory[IMarketplaceAspects]({Marketplace.EBAY: EbayAspects})
