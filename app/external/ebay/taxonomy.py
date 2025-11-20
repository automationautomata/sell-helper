import json
import os

import requests

from ...config import EbayDomain
from ...data import EnvKeys
from ...utils import utils
from .errors import EbayRequestError
from .models import (
    AspectMetadata,
    CategorySuggestionResponse,
    CategoryTree,
    MarketplaceIdEnum,
)

API_ENDPOINT = "/commerce/taxonomy/v1"


class EbayTaxonomyClientError(EbayRequestError):
    pass


class EbayCategoriesNotFoundError(EbayRequestError):
    pass


class EbayTaxonomyClient:
    def __init__(self, domain: EbayDomain):  # type: ignore
        self._url_base = f"https://{domain}{API_ENDPOINT}"

    @utils.request_exception_chain(default=EbayTaxonomyClientError)
    def get_default_tree_id(self, marketplace_id: MarketplaceIdEnum) -> str:
        if marketplace_id == MarketplaceIdEnum.EBAY_MOTORS:
            marketplace_id = "EBAY_MOTORS_US"

        url = f"{self._url_base}/get_default_category_tree_id"
        params = {"marketplace_id": marketplace_id}
        headers = {
            "Authorization": f"Bearer {os.getenv(EnvKeys.EBAY_USER_TOKEN)}",
        }
        resp = requests.get(url, params=params, headers=headers)
        resp.raise_for_status()
        data = resp.json()
        return data["categoryTreeId"]

    @utils.request_exception_chain(default=EbayTaxonomyClientError)
    def fetch_category_tree(self, tree_id: str) -> CategoryTree:
        """Retrieve the complete category tree for a specific eBay marketplace.

        Args:
            tree_id (str): The ID of the category tree to retrieve

        Returns:
            CategoryTree: Complete category tree with root node and all child categories

        Raises:
            EbayTaxonomyClientError: If the request fails
        """
        url = f"{self._url_base}/category_tree/{tree_id}"
        headers = {
            "Authorization": f"Bearer {os.getenv(EnvKeys.EBAY_USER_TOKEN)}",
            "Accept-Encoding": "gzip",
        }

        resp = requests.get(url, headers=headers)
        resp.raise_for_status()

        with open("categories.json", "w+") as f:
            f.write(json.dumps(resp.json()))
        return CategoryTree.model_validate(resp.json())

    @utils.request_exception_chain(default=EbayTaxonomyClientError)
    def get_item_aspects(
        self, category_tree_id: str, category_id: str
    ) -> AspectMetadata:
        """Get detailed information about category-specific aspects.

        Args:
            category_tree_id (str): The ID of the eBay category tree
            category_id (str): The ID of the category to get aspects for

        Returns:
            AspectMetadata: Detailed aspect metadata including constraints and valid values

        Raises:
            EbayTaxonomyClientError: If the request fails
        """
        resp = requests.get(
            url=f"{self._url_base}/category_tree/{category_tree_id}/get_item_aspects_for_category",
            params={"category_id": category_id},
            headers={
                "Authorization": f"Bearer {os.getenv(EnvKeys.EBAY_USER_TOKEN)}",
            },
        )
        resp.raise_for_status()
        return AspectMetadata.model_validate(resp.json())

    @utils.request_exception_chain(
        default=EbayTaxonomyClientError, on_http=EbayCategoriesNotFoundError
    )
    def get_category_suggestions(
        self, category_tree_id: str, query: str
    ) -> CategorySuggestionResponse:
        """Get category suggestions based on a query string.

        Args:
            category_tree_id (str): The ID of the eBay category tree for the marketplace
            query (str): The string to get category suggestions for

        Returns:
            CategorySuggestionResponse: The category suggestions response containing matched categories

        Raises:
            EbayTaxonomyClientError: If the request fails
        """
        resp = requests.get(
            url=f"{self._url_base}/category_tree/{category_tree_id}/get_category_suggestions",
            params={"q": query},
            headers={
                "Authorization": f"Bearer {os.getenv(EnvKeys.EBAY_USER_TOKEN)}",
            },
        )
        return CategorySuggestionResponse.model_validate(resp.json())
