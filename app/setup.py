from datetime import timedelta

from dishka import AsyncContainer, make_async_container
from dishka.integrations.fastapi import FastapiProvider
from fastapi import FastAPI
from passlib.hash import pbkdf2_sha256

from app.api import AppBuilder
from app.config import Config, DBConfig, EbayConfig, RedisConfig
from app.infrastructure.providers import (
    EbayInfrastructureProvider,
    FactoriesProvider,
    InfrastructureProvider,
    JWTAuthSettings,
    OAuthStateAuthProvider,
    OAuthStateAuthSettings,
    SearchEngineSettings,
)
from app.providers import (
    DBProvider,
    EbayProvider,
    MarketplaceMappingsProvider,
    OAuthProvider,
    PerplexityClientProvider,
    PerplexityToken,
    RedisProvider,
)
from app.repository.providers import RepositoryProvider
from app.services.ports import IHasher
from app.services.providers import (
    SellingServiceSettings,
    ServicesProvider,
)


def load_config() -> Config:
    return Config()


def app(config: Config) -> FastAPI:
    builder = AppBuilder(root_path="/api")
    builder.root_router().middlewares(config.secrets)
    return builder.get_app()


def container(config: Config) -> AsyncContainer:
    providers = [
        DBProvider(),
        RedisProvider(),
        OAuthProvider(),
        EbayProvider(),
        MarketplaceMappingsProvider(),
        PerplexityClientProvider(),
        InfrastructureProvider(),
        EbayInfrastructureProvider(),
        OAuthStateAuthProvider(),
        RepositoryProvider(),
        ServicesProvider(),
        FactoriesProvider(),
        FastapiProvider(),
    ]

    ext_services = config.external_services
    context = {
        DBConfig: config.db,
        RedisConfig: config.redis,
        EbayConfig: ext_services.ebay,
        PerplexityToken: config.tokens.perplexity_token,
        SearchEngineSettings: SearchEngineSettings(
            barcode_search_token=config.tokens.barcode_search_token,
            perplexity_model=ext_services.perplexity.model,
        ),
        SellingServiceSettings: SellingServiceSettings(
            token_ttl_threshold=timedelta(hours=1, minutes=40).total_seconds()
        ),
        OAuthStateAuthSettings: OAuthStateAuthSettings(5, "HS256", config.secrets.jwt),
        JWTAuthSettings: JWTAuthSettings(20, "HS256", config.secrets.jwt),
        IHasher: pbkdf2_sha256,
    }
    return make_async_container(*providers, context=context)
