import statistics
from types import SimpleNamespace

import pytest
from pytest_mock import mocker

from app.core.services.price_statistics.price_statistics import (
    ItemInfo,
    Price,
    PriceStatisticsService,
)


def test_calc_statistics_same_currency(mocker):
    values = [10.0, 20.0, 20.0]
    currency = "USD"
    prices = [Price(value=v, currency=currency) for v in values]

    converter_mock = mocker.Mock()
    converter_mock.convert.return_value = values

    strategy_mock = mocker.Mock()
    strategy_mock.get_prices.return_value = prices

    service = PriceStatisticsService(strategy_mock, converter_mock)
    item = ItemInfo(name="phone", currency="USD", category_name="")
    stats = service.calc_statistics(item)

    assert pytest.approx(stats.mean_price, rel=1e-9) == statistics.mean(values)
    assert pytest.approx(stats.mode_price, rel=1e-9) == statistics.mode(values)
    assert pytest.approx(stats.median_price, rel=1e-9) == statistics.median(values)
    assert pytest.approx(stats.min_price, rel=1e-9) == min(values)
    assert pytest.approx(stats.max_price, rel=1e-9) == max(values)


def test_calc_statistics_with_conversion(mocker):
    dst_currency = "USD"
    prices = [
        Price(value=10.0, currency=dst_currency),
        Price(value=1100.0, currency="JPY"),
    ]

    strategy_mock = mocker.Mock()
    strategy_mock.get_prices.return_value = prices

    converter_mock = mocker.Mock()
    converter_mock.convert.return_value = [10.0]

    service = PriceStatisticsService(strategy_mock, converter_mock)

    item = ItemInfo(name="phone", currency=dst_currency, category_name="")

    stats = service.calc_statistics(item)

    values = [10.0, 10.0]
    assert pytest.approx(stats.mean_price, rel=1e-9) == statistics.mean(values)
    assert pytest.approx(stats.mode_price, rel=1e-9) == statistics.mode(values)
    assert pytest.approx(stats.median_price, rel=1e-9) == statistics.median(values)
    assert pytest.approx(stats.min_price, rel=1e-9) == min(values)
    assert pytest.approx(stats.max_price, rel=1e-9) == max(values)
    converter_mock.convert.assert_called_once()
