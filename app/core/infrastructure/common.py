from dataclasses import dataclass
from typing import Optional

from ...external.ebay import models as ebay_models
from ...external.ebay.taxonomy import EbayTaxonomyClient


@dataclass
class CategoryDTO:
    tree_id: str
    category_id: str
    category_name: str


class EbayUtils:
    def __init__(self, taxonomy_api: EbayTaxonomyClient):
        self._taxonomy_api = taxonomy_api

    def get_category_id(
        self, category_name: str, marketplace_id: str
    ) -> Optional[CategoryDTO]:
        tree_id = self._taxonomy_api.get_default_tree_id(marketplace_id)
        tree = self._taxonomy_api.fetch_category_tree(tree_id)
        res = self._search_ebay_category(tree, category_name)
        if res is None:
            return None

        return CategoryDTO(tree_id=tree_id, category_id=res[0], category_name=res[1])

    @staticmethod
    def _search_ebay_category(
        tree: ebay_models.CategoryTree, target: str
    ) -> tuple[str, str] | None:
        """Recursively search the node and its children for categoryName matches
        and returns categoryId and categoryName."""

        def search(n: ebay_models.CategoryTreeNode) -> tuple[str, str] | None:
            if n.leaf_category_tree_node:
                category = n.category
                name = category.category_name

                if name and target.lower() == name.lower():
                    return category.category_id, name

            for child in n.child_category_tree_nodes:
                res = search(child)
                if res:
                    return res

            return None

        return search(tree.root_category_node)
