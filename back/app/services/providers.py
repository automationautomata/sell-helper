from dataclasses import dataclass
from typing import Annotated

from dishka import FromComponent, Provider, Scope, from_context, provide

from app.domain.ports import (
    IAuthService,
    IMarketplaceAccountService,
    IMarketplaceOAuthService,
    IRegistrationService,
    ISearchService,
    ISellingService,
)

from . import ports
from .auth import AuthService
from .common import MarketplaceTokenManager
from .marketplace_account import MarketplaceAccountService
from .marketplace_oauth import MarketplaceOAuthService
from .search import SearchService
from .selling import SellingService


@dataclass
class TokenUpdateSettings:
    token_ttl_threshold: int


class ServicesProvider(Provider):
    token_update_settings = from_context(TokenUpdateSettings, scope=Scope.APP)

    @provide(scope=Scope.REQUEST)
    def token_maneger(
        self,
        access_token_storage: ports.IAccessTokenStorage,
        refresh_token_storage: ports.IRefreshTokenStorage,
        oauth_factory: ports.IMarketplaceOAuthFactory,
        settings: TokenUpdateSettings,
    ) -> MarketplaceTokenManager:
        return MarketplaceTokenManager(
            oauth_factory=oauth_factory,
            refresh_token_storage=refresh_token_storage,
            access_token_storage=access_token_storage,
            token_ttl_threshold=settings.token_ttl_threshold,
        )

    search_service = provide(
        SearchService, provides=ISearchService, scope=Scope.REQUEST
    )

    account_service = provide(
        MarketplaceAccountService,
        provides=IMarketplaceAccountService,
        scope=Scope.REQUEST,
    )
    selling_service = provide(
        SellingService, provides=ISellingService, scope=Scope.REQUEST
    )

    auth_service = provide(AuthService, scope=Scope.REQUEST)

    @provide(scope=Scope.REQUEST)
    def auth_service_iterface(self, auth_service: AuthService) -> IAuthService:
        return auth_service

    @provide(scope=Scope.REQUEST)
    def reg_service_iterface(self, auth_service: AuthService) -> IRegistrationService:
        return auth_service

    @provide(scope=Scope.REQUEST)
    def marketplace_auth(
        self,
        user_repo: ports.IUserRepository,
        access_token_storage: ports.IAccessTokenStorage,
        refresh_token_storage: ports.IRefreshTokenStorage,
        oauth_factory: ports.IMarketplaceOAuthFactory,
        jwt_auth: Annotated[ports.IJWTAuth, FromComponent("oauth_state_auth")],
    ) -> IMarketplaceOAuthService:
        return MarketplaceOAuthService(
            user_repo=user_repo,
            jwt_auth=jwt_auth,
            access_token_storage=access_token_storage,
            refresh_token_storage=refresh_token_storage,
            oauth_factory=oauth_factory,
        )
