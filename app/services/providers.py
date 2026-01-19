from dataclasses import dataclass

from dishka import FromComponent, Provider, Scope, from_context, provide

from app.domain.ports import (
    IAuthService,
    IMarketplaceOAuthService,
    IRegistrationService,
    ISearchService,
    ISellingService,
)

from . import ports
from .auth import AuthService
from .marketplace_oauth import MarketplaceOAuthService
from .search import SearchService
from .selling import SellingService


@dataclass
class SellingServiceSettings:
    token_ttl_threshold: int


class ServicesProvider(Provider):
    selling_settings = from_context(SellingServiceSettings, scope=Scope.APP)

    search_service = provide(
        SearchService, provides=ISearchService, scope=Scope.REQUEST
    )
    auth_service = provide(AuthService, scope=Scope.REQUEST)

    @provide(scope=Scope.REQUEST)
    def auth_service_iface(self, auth_service: AuthService) -> IAuthService:
        return auth_service

    @provide(scope=Scope.REQUEST)
    def reg_service_iface(self, auth_service: AuthService) -> IRegistrationService:
        return auth_service

    @provide(scope=Scope.REQUEST)
    def marketplace_auth(
        self,
        user_repo: ports.IUserRepository,
        access_token_storage: ports.IAccessTokenStorage,
        refresh_token_storage: ports.IRefreshTokenStorage,
        oauth_factory: ports.IMarketplaceOAuthFactory,
        jwt_auth: ports.IJWTAuth = FromComponent("oauth_state_auth"),
    ) -> IMarketplaceOAuthService:
        return MarketplaceOAuthService(
            user_repo=user_repo,
            jwt_auth=jwt_auth,
            access_token_storage=access_token_storage,
            refresh_token_storage=refresh_token_storage,
            oauth_factory=oauth_factory,
        )

    @provide(scope=Scope.REQUEST)
    def selling_service(
        self,
        api_factory: ports.IMarketplaceAPIFactory,
        access_token_storage: ports.IAccessTokenStorage,
        refresh_token_storage: ports.IRefreshTokenStorage,
        oauth_factory: ports.IMarketplaceOAuthFactory,
        selling_settings: SellingServiceSettings,
        marketplace_aspects_factory: ports.IMarketplaceAspectsFactory,
    ) -> ISellingService:
        return SellingService(
            api_factory=api_factory,
            access_token_storage=access_token_storage,
            refresh_token_storage=refresh_token_storage,
            oauth_factory=oauth_factory,
            token_ttl_threshold=selling_settings.token_ttl_threshold,
            type_factory=marketplace_aspects_factory,
        )
