from dataclasses import dataclass

from dishka import Provider, Scope, from_context, provide
from perplexity import Perplexity as PerplexityClient

from ...config import EbayConfig
from ..services.ports import IHasher, IJWTAuth, IMarketplaceAPI, ISearchEngine
from .jwt_auth import JWTAuth
from .marketplace import EbayAPI, EbayClients
from .search import PerplexityAndEbaySearch


@dataclass
class JWTAuthSettings:
    jwt_ttl_minutes: int
    jwt_algorithm: str


class JWTAuthProvider(Provider):
    jwt_settings = from_context(JWTAuthSettings, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def jwt_auth(self, jwt_settings: JWTAuthSettings) -> IJWTAuth:
        return JWTAuth(
            jwt_settings.jwt_ttl_minutes,
            jwt_settings.jwt_algorithm,
        )

@dataclass
class PerplexitySettings:
    model: str


class EbayInfrastructureProvider(Provider):
    component = "ebay"

    @provide(scope=Scope.APP)
    def search(
        self,
        perplexity_config: PerplexitySettings,
        perplexity_client: PerplexityClient,
        ebay_config: EbayConfig,
        ebay_clients: EbayClients,
    ) -> ISearchEngine:
        return PerplexityAndEbaySearch(
            perplexity_config,
            perplexity_client,
            ebay_config.marketplace_id,
            ebay_clients.taxonomy_client,
        )

    @provide(scope=Scope.APP)
    def merketplace(
        self, ebay_config: EbayConfig, clients: EbayClients
    ) -> IMarketplaceAPI:
        return EbayAPI(ebay_config, clients)
