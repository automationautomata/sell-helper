from typing import Optional

from ...infrastructure.ebay_items_fetch import EbayCondition, FetchEbayItemsABC
from .price_statistics import ItemInfo, Price


class EbayPricesSearchStrategy:
    def __init__(self, fetch_ebay_items: FetchEbayItemsABC):
        self._fetch_ebay_items = fetch_ebay_items

    def get_prices(
        self, item_info: ItemInfo, *, condition: Optional[str] = None
    ) -> list[Price]:
        items = self._fetch_ebay_items.get_items(
            item_info.name, item_info.category_name
        )

        filtered_items = self._apply_filters(items, condition=condition)
        return [
            Price(value=item.price, currency=item.currency) for item in filtered_items
        ]

    def _apply_filters(self, items: list, *, condition: Optional[str] = None) -> list:
        filtered = items
        if condition is not None:
            condition = EbayCondition(condition)
            filtered = [item for item in filtered if item.condition == condition]

        return filtered
