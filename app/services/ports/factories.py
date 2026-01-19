from typing import Protocol

from ...domain.entities import IMarketplaceAspects, IMetadata
from .interfaces import ICategoryPredictor, IMarketplaceAPI, IMarketplaceOAuth


class IFactory[T](Protocol):
    def get(self, marketplace: str) -> T:
        pass


IMarketplaceAPIFactory = IFactory[IMarketplaceAPI]


ICategoryPredictorFactory = IFactory[ICategoryPredictor]


IMarketplaceOAuthFactory = IFactory[IMarketplaceOAuth]


IMarketplaceAspectsFactory = IFactory[type[IMarketplaceAspects]]


IMetadataFactory = IFactory[type[IMetadata]]
