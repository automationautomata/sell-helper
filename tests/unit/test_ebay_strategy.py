from types import SimpleNamespace

from pytest_mock import mocker
from app.core.services.price_statistics.ebay_strategy import (
    EbayPricesSearchStrategy,
)
from app.core.infrastructure.ebay_items_fetch import EbayCondition, EbayItemDTO
from app.core.services.price_statistics.price_statistics import ItemInfo


def make_item(price, currency, condition_str):
    return SimpleNamespace(
        price=price, currency=currency, condition=EbayCondition(condition_str)
    )


def test_get_prices_no_filter(mocker):
    items = [
        EbayItemDTO("laptop", 10, "USD", "NEW"),
        EbayItemDTO("phone", 20, "USD", "USED"),
    ]
    fetch_mock = mocker.Mock()
    fetch_mock.get_items.return_value = items
    strategy = EbayPricesSearchStrategy(fetch_mock)

    prices = strategy.get_prices(ItemInfo(name="x", currency="USD", category_name=""))
    assert len(prices) == 2
    assert prices[0].value == 10
    assert prices[1].value == 20


def test_get_prices_with_condition_filter(mocker):
    items = [
        make_item(10, "USD", "NEW"),
        make_item(20, "USD", "USED"),
        make_item(30, "USD", "NEW"),
    ]
    fetch = mocker.Mock()
    fetch.get_items.return_value = items
    strategy = EbayPricesSearchStrategy(fetch)

    prices = strategy.get_prices(
        ItemInfo(name="x", currency="USD", category_name=""), condition="NEW"
    )
    assert len(prices) == 2
    assert [p.value for p in prices] == [10, 30]
