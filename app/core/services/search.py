from app.core.domain.ports import (
    ProductCategories,
    ProductCategoriesNotFoundError,
    SearchError,
)

from ..domain.entities.question import Answer, ProductStructure, Question, TMetadata
from .ports import (
    CategoriesNotFoundError,
    IMarketplaceAPI,
    ISearchEngine,
    SearchEngineError,
)


class SearchService:
    def __init__(
        self,
        search: ISearchEngine,
        marketplace_api: IMarketplaceAPI,
        metadata_type: TMetadata,
    ) -> None:
        self._search = search
        self._marketplace_api = marketplace_api
        self._metadata_type = metadata_type

    def product(self, product_name: str, category: str, comment: str) -> Answer:
        aspects = self._marketplace_api.get_product_aspects(category)

        q = Question(
            product_structure=ProductStructure(aspects),
            metadata_type=self._metadata_type,
        )

        try:
            return self._search.by_product_name(product_name, comment, q)
        except SearchEngineError as e:
            raise SearchError() from e

    def product_categories(self, img_path: str) -> ProductCategories:
        barecodes = self._search.barecodes_on_image(img_path)
        if len(barecodes) != 1:
            raise SearchError("Image must contain exactly one barcode")

        try:
            product_name = self._search.by_barecode(barecodes[0])
            categories = self._search.categories(product_name)
        except CategoriesNotFoundError as e:
            raise ProductCategoriesNotFoundError() from e
        except SearchEngineError as e:
            raise SearchError() from e

        return ProductCategories(product_name, categories)
