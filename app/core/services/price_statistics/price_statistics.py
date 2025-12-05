import statistics
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Protocol, final

from ...infrastructure.currency import (
    Currency,
    CurrencyConverterABC,
    CurrencyConverterError,
)


class StatisticsServiceError(Exception):
    pass


class StrategyError(Exception):
    pass


@dataclass
class ItemInfo:
    name: str
    currency: str
    category_name: str


@dataclass
class Price:
    value: float
    currency: str


@final
@dataclass
class Statistics:
    mean_price: float
    mode_price: float
    median_price: float
    min_price: float
    max_price: float


class IPricesSearchStrategy(Protocol):
    def get_prices(self, item_info: ItemInfo, **filters: Any) -> list[Price]:
        pass


class PriceStatisticsServiceABC(ABC):
    @abstractmethod
    def calc_statistics(self, item_info: ItemInfo, **filters: Any) -> Statistics:
        pass


class PriceStatisticsService(PriceStatisticsServiceABC):
    def __init__(
        self,
        strategy: IPricesSearchStrategy,
        currency_converter: CurrencyConverterABC,
    ):
        self._strategy = strategy
        self._currency_converter = currency_converter

    def calc_statistics(self, item_info: ItemInfo, **filters: Any) -> Statistics:
        """Calculate statistics for an item.

        Args:
            item_info: Item information (name, currency, category)
            **filters: Strategy-specific filters passed by application layer
                      (condition='NEW' for EBay strategy)
        """
        try:
            prices = self._strategy.get_prices(item_info, **filters)
        except StrategyError as e:
            raise StatisticsServiceError() from e

        prices_to_convert = {}
        for p in prices:
            if p.currency not in prices_to_convert:
                prices_to_convert[p.currency] = []
            prices_to_convert[p.currency].append(p.value)

        currency = item_info.currency
        values = prices_to_convert.pop(currency, [])

        if len(prices_to_convert) != 0:
            try:
                currencies_values = []
                for k, v in prices_to_convert.items():
                    currencies_values.append(Currency(name=k, values=v))

                values += self._currency_converter.convert(currency, *currencies_values)
            except CurrencyConverterError as e:
                raise StatisticsServiceError() from e

        return Statistics(
            max_price=max(values),
            min_price=min(values),
            mean_price=statistics.mean(values),
            mode_price=statistics.mode(values),
            median_price=statistics.median(values),
        )
