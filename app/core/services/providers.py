from typing import Type

from dishka import Provider, Scope, from_context, provide

from ..domain.entities.ebay.item import EbayMarketplaceAspects
from ..domain.entities.ebay.question import EbayMetadata
from ..domain.entities.item import MarketplaceAspects
from ..domain.entities.question import Metadata
from ..domain.ports import IAuthService, ISearchService, ISellingService
from ..services.ports import (
    IHasher,
    IJWTAuth,
    IMarketplaceAPI,
    ISearchEngine,
    IUsersRepository,
)
from .auth import AuthService
from .search import SearchService
from .selling import SellingService


class AuthServiceProvider(Provider):
    hasher = from_context(IHasher, scope=Scope.APP)

    @provide(scope=Scope.REQUEST)
    def auth_service(
        self, hasher: IHasher, user_repo: IUsersRepository, jwt_auth: IJWTAuth
    ) -> IAuthService:
        return AuthService(hasher, user_repo, jwt_auth)


class ServicesProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def search_service(
        self,
        search_engine: ISearchEngine,
        marketplace_api: IMarketplaceAPI,
        metadata_type: Type[Metadata],
    ) -> ISearchService:
        return SearchService(search_engine, marketplace_api, metadata_type)

    @provide(scope=Scope.REQUEST)
    def selling_service(
        self,
        marketplace_api: IMarketplaceAPI,
        marketplace_aspects_type: Type[MarketplaceAspects],
    ) -> ISellingService:
        return SellingService(marketplace_api, marketplace_aspects_type)


# class EbayServicesProvider(ServicesProvider):
#     component = "ebay"


