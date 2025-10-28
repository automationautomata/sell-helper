from dataclasses import dataclass
from typing import Dict, Type

from core.domain.item import TMarketplaceAspects
from core.domain.question import TMetadata
from core.infrastructure.adapter import QuestionAdapterABC
from core.infrastructure.marketplace import MarketplaceAPI
from core.infrastructure.search import SearchEngineABC
from core.services.search import SearchService, SearchServiceABC
from core.services.selling import SellingService, SellingServiceABC
from dishka import Provider, Scope, from_context, provide
from fastapi import Request


@dataclass
class SearchSettings:
    search_engine: SearchEngineABC
    marketplace_api: MarketplaceAPI
    question_adapter: QuestionAdapterABC
    metadata_type: Type[TMetadata]


@dataclass
class SearchSettingsMap:
    map: Dict[str, SearchSettings]


@dataclass
class SellingSettings:
    marketplace_api: MarketplaceAPI
    marketplace_aspects_type: type[TMarketplaceAspects]


@dataclass
class SellingSettingsMap:
    map: Dict[str, SellingSettings]


class SearchServiceProvider(Provider):
    settings_map = from_context(SearchSettingsMap, scope=Scope.APP)

    @provide(scope=Scope.REQUEST)
    def get_selling_service(
        self, request: Request, settings_map: SearchSettingsMap
    ) -> SearchServiceABC:
        marketplace = request.path_params.get("marketplace")

        if marketplace not in settings_map.map:
            raise ValueError(f"Unsupported marketplace: {marketplace}")

        s = settings_map.map[marketplace]
        return SearchService(
            search=s.search_engine,
            marketplace_api=s.marketplace_api,
            adapter=s.question_adapter,
            metadata_type=s.metadata_type,
        )


class SellingServiceProvider(Provider):
    settings_map = from_context(provides=SellingSettingsMap, scope=Scope.APP)

    @provide(scope=Scope.REQUEST)
    def get_selling_service(
        self, request: Request, settings_map: SellingSettingsMap
    ) -> SellingServiceABC:
        marketplace = request.path_params.get("marketplace")

        if marketplace not in settings_map.map:
            raise ValueError(f"Unsupported marketplace: {marketplace}")

        s = settings_map.map[marketplace]
        return SellingService(
            marketplace_api=s.marketplace_api,
            marketplace_aspects_type=s.marketplace_aspects_type,
        )
