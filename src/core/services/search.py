from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..domain.question import Answer, ProductStructure, Question, TMetadata
from ..infrastructure.adapter import InvalidProduct, QuestionAdapterABC, ValidationError
from ..infrastructure.marketplace import MarketplaceAPI
from ..infrastructure.search import (
    CategoriesNotFoundError,
    SearchEngineABC,
    SearchEngineError,
)


class SearchError(Exception):
    pass


class ProductCategoriesNotFoundError(Exception):
    pass


@dataclass(frozen=True)
class ProductCategories:
    product_name: str
    categories: list[str]


class SearchServiceABC(ABC):
    DEAFULT_QUESTION = "Provide information by the image"

    @abstractmethod
    def product(self, product_name: str, category: str, comment: str) -> Answer:
        """Search product by name and category"""
        pass

    @abstractmethod
    def product_categories(self, img_path: str) -> ProductCategories:
        """Search categories by product name"""
        pass


class SearchService(SearchServiceABC):
    def __init__(
        self,
        search: SearchEngineABC,
        marketplace_api: MarketplaceAPI,
        adapter: QuestionAdapterABC,
        metadata_type: TMetadata,
    ) -> None:
        self._adapter = adapter
        self._search = search
        self._marketplace_api = marketplace_api
        self._metadata_type = metadata_type

    def product(self, product_name: str, category: str, comment: str) -> Answer:
        aspects = self._marketplace_api.get_product_aspects(category)

        q = Question(
            product_structure=ProductStructure(aspects),
            metadata_type=self._metadata_type,
        )
        schema = self._adapter.to_schema(q)

        try:
            raw_data = self._search.by_product_name(product_name, comment, schema)
        except SearchEngineError as e:
            raise SearchError() from e

        try:
            return self._adapter.to_answer(raw_data, q)

        except InvalidProduct as e:
            raise SearchError("Failed to parse product aspects data") from e

        except ValidationError as e:
            raise SearchError("Failed to parse product metadata") from e

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
