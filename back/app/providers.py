import uuid
from collections.abc import AsyncIterable
from itertools import count
from typing import Annotated

from authlib.integrations.starlette_client import OAuth, StarletteOAuth2App
from dishka import (
    FromComponent,
    Provider,
    Scope,
    from_context,
    provide,
)
from perplexity import Perplexity as PerplexityClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.dependencies import OAuth2ClientMapping
from app.config import DBConfig, EbayConfig, RedisConfig
from app.data import Marketplace, OAuth2Settings
from app.infrastructure.providers import EbayClientSettings, SKUGenerator


class DBProvider(Provider):
    db_config = from_context(DBConfig, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def get_session_maker(
        self, db_config: DBConfig
    ) -> async_sessionmaker[AsyncSession]:
        engine = create_async_engine(db_config.get_url())
        return async_sessionmaker(engine, expire_on_commit=False)

    @provide(scope=Scope.REQUEST)
    async def get_session(
        self, session_maker: async_sessionmaker[AsyncSession]
    ) -> AsyncIterable[AsyncSession]:
        async with session_maker() as session:
            yield session


class RedisProvider(Provider):
    redis_config = from_context(RedisConfig, scope=Scope.APP)

    @provide(scope=Scope.REQUEST)
    def redis(self, redis_config: RedisConfig) -> Redis:
        return Redis.from_url(redis_config.get_url())


PerplexityToken = str


class PerplexityClientProvider(Provider):
    perplexity_token = from_context(PerplexityToken, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def perplexity_client(self, perplexity_token: PerplexityToken) -> PerplexityClient:
        return PerplexityClient(api_key=perplexity_token)


class OAuthProvider(Provider):
    @provide(scope=Scope.APP)
    def oauth(self) -> OAuth:
        return OAuth()


class EbayProvider(Provider):
    component = "ebay"
    ebay_config = from_context(EbayConfig, scope=Scope.APP)

    @provide(scope=Scope.APP)
    def sku_generator(self) -> SKUGenerator:
        return (uuid.uuid4().hex.upper() for _ in count())

    @provide(scope=Scope.APP)
    def oauth2_settings(self, ebay_config: EbayConfig) -> OAuth2Settings:
        scopes = [
            f"https://{ebay_config.domain}/oauth/api_scope",
            f"https://{ebay_config.domain}/oauth/api_scope/sell.account",
            f"https://{ebay_config.domain}/oauth/api_scope/sell.inventory",
        ]
        return OAuth2Settings(
            client_id=ebay_config.appid,
            client_secret=ebay_config.certid,
            redirect_uri=ebay_config.redirect_uri,
            authorize_url=f"https://{ebay_config.domain}/oauth2/authorize",
            access_token_url=f"https://{ebay_config.domain}/identity/v1/oauth2/token",
            scope=" ".join(scopes),
        )

    @provide(scope=Scope.APP)
    def ebay_clients_settings(
        self, ebay_config: EbayConfig, settings: OAuth2Settings
    ) -> EbayClientSettings:
        return EbayClientSettings(ebay_config.domain, settings)

    @provide(scope=Scope.APP)
    def starlette_oauth(
        self, settings: OAuth2Settings, oauth: Annotated[OAuth, FromComponent("")]
    ) -> StarletteOAuth2App:
        return oauth.register(
            name="ebay",
            **settings,
            token_endpoint_auth_method="client_secret_basic",
        )


class MarketplaceMappingsProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def oauth2_factory(
        self, ebay_oauth: Annotated[StarletteOAuth2App, FromComponent("ebay")]
    ) -> OAuth2ClientMapping:
        return {Marketplace.EBAY: ebay_oauth}
