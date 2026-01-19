from dataclasses import dataclass

from app.services.ports import CategoriesNotFoundError, CategoryPredictorError

from .api_clients.ebay import (
    EbayCategoriesNotFoundError,
    EbayTaxonomyClient,
    EbayTaxonomyClientError,
)


@dataclass
class EbayCategoryPredictor:
    taxonomy_api: EbayTaxonomyClient

    def predict(
        self, product_name: str, *, marketplace: str | None = None
    ) -> list[str]:
        if marketplace is None:
            raise ValueError("Marketplace must be specified")

        try:
            tree_id = self.taxonomy_api.get_default_tree_id(marketplace)

            resp = self.taxonomy_api.get_category_suggestions(tree_id, product_name)

            categories = []
            for suggestion in resp.category_suggestions:
                categories.append(suggestion.category.category_name)

            return categories

        except EbayTaxonomyClientError as e:
            raise CategoryPredictorError(
                "Failed to get ebay category suggestions"
            ) from e

        except EbayCategoriesNotFoundError as e:
            raise CategoriesNotFoundError() from e
