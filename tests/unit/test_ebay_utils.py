from types import SimpleNamespace

import pytest

from app.core.infrastructure.common import EbayUtils, CategoryDTO
from app.external.ebay import models as ebay_models


def make_tree_with_child(cat_id, cat_name, leaf=True):
    return ebay_models.CategoryTree(
        applicable_marketplace_ids=["EBAY_US"],
        category_tree_id="tree123",
        category_tree_version="v1",
        root_category_node=ebay_models.CategoryTreeNode(
            category=ebay_models.Category(category_id="root", category_name="root"),
            category_tree_node_level=1,
            child_category_tree_nodes=[
                ebay_models.CategoryTreeNode(
                    category=ebay_models.Category(
                        category_id=cat_id, category_name=cat_name
                    ),
                    category_tree_node_level=2,
                    leaf_category_tree_node=leaf,
                    child_category_tree_nodes=[],
                )
            ],
            leaf_category_tree_node=False,
        ),
    )


def test_get_category_id_found(mocker):
    taxonomy = mocker.Mock()
    taxonomy.get_default_tree_id.return_value = "tree123"
    taxonomy.fetch_category_tree.return_value = make_tree_with_child("cat2", "Phones")

    utils = EbayUtils(taxonomy)
    res = utils.get_category_id("Phones", "EBAY_US")

    assert isinstance(res, CategoryDTO)
    assert res.category_id == "cat2"
    assert res.category_name == "Phones"


def test_get_category_id_not_found(mocker):
    taxonomy = mocker.Mock()
    taxonomy.get_default_tree_id.return_value = "tree123"
    taxonomy.fetch_category_tree.return_value = make_tree_with_child(
        "cat1", "Electronics"
    )

    utils = EbayUtils(taxonomy)
    res = utils.get_category_id("NonExistent", "EBAY_US")

    assert res is None


def test_search_category_case_insensitive():
    tree = make_tree_with_child("cat1", "Electronics")
    res = EbayUtils._search_ebay_category(tree, "electronics")
    assert res == ("cat1", "Electronics")
