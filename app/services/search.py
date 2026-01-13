from dataclasses import dataclass

from ..domain.dto import ProductCategoriesDTO, ProductDTO
from ..domain.entities import ProductStructure
from ..domain.ports import (
    ProductCategoriesNotFoundError,
    SearchServiceError,
)
from .mapping import FromEntity
from .ports import (
    CategoriesNotFoundError,
    ICategoryPredictorFactory,
    IMarketplaceAPIFactory,
    ISearchEngine,
    SearchEngineError,
)


@dataclass
class SearchService:
    search: ISearchEngine
    api_factory: IMarketplaceAPIFactory
    predictors_factory: ICategoryPredictorFactory

    def product_aspects(
        self,
        product_name: str,
        category: str,
        comment: str,
        marketplace,
        **settings: dict,
    ) -> ProductDTO:
        try:
            marketplace_api = self.api_factory.get(marketplace)
            aspects = marketplace_api.get_product_aspects(category, **(settings or {}))

            product = self.search.by_product_name(
                product_name, ProductStructure(aspects), comment
            )
            return FromEntity.product_dto(product)
        except SearchEngineError as e:
            raise SearchServiceError() from e

    def recognize_product(
        self, img_path: str, marketplace: str, **settings: dict
    ) -> ProductCategoriesDTO:
        barecodes = self.search.barecodes_on_image(img_path)
        if len(barecodes) != 1:
            raise SearchServiceError("Image must contain exactly one barcode")

        try:
            category_predictor = self.predictors_factory.get(marketplace)
            product_name = self.search.product_name_by_barecode(barecodes[0])
            categories = category_predictor.predict(product_name, **(settings or {}))

            return ProductCategoriesDTO(product_name, categories)

        except CategoriesNotFoundError as e:
            raise ProductCategoriesNotFoundError() from e

        except SearchEngineError as e:
            raise SearchServiceError() from e
