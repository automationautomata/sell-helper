from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from ...external.ebay.browse import EbayBrowseClient, EbayBrowseClientError
from ...external.ebay.taxonomy import EbayTaxonomyClient, EbayTaxonomyClientError
from .common import EbayUtils


class FetchEbayItemsError(Exception):
    pass


class EbayCondition(str, Enum):
    NEW = "NEW"
    USED = "USED"


@dataclass
class EbayItemDTO:
    name: str
    price: float
    currency: str
    condition: EbayCondition


class FetchEbayItemsABC(ABC):
    @abstractmethod
    def get_items(self, name: str, category_name: str) -> list[EbayItemDTO]:
        pass


class FetchEbayItems(FetchEbayItemsABC):
    def __init__(
        self,
        taxonomy_api: EbayTaxonomyClient,
        browse_api: EbayBrowseClient,
        marketplace_id: str,
    ):
        self._taxonomy_api = taxonomy_api
        self._browse_api = browse_api
        self._marketplace_id = marketplace_id

    def get_items(self, name: str, category_name: str) -> list[EbayItemDTO]:
        try:
            utils = EbayUtils(self._taxonomy_api)
            category_dto = utils.get_category_id(category_name, self._marketplace_id)
            resp = self._browse_api.search_items(
                name, categories_ids=[category_dto.category_id]
            )
        except (EbayTaxonomyClientError, EbayBrowseClientError) as e:
            raise FetchEbayItemsError() from e

        if not resp.item_summaries:
            return []

        def from_ebay_condition(condition):
            if 'new' in condition.lower():
                return EbayCondition.NEW 
            return EbayCondition.USED

        items = []
        for summary in resp.item_summaries:
            items.append(
                EbayItemDTO(
                    name=summary.title,
                    price=float(summary.price.value),
                    currency=summary.price.currency,
                    condition=from_ebay_condition(summary.condition),
                )
            )

        return items
