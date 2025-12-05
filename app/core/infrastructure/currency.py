from abc import ABC, abstractmethod
from dataclasses import dataclass

import requests
from requests.exceptions import ConnectionError, HTTPError, RequestException, Timeout


class CurrencyConverterError(Exception):
    pass


class CurrencyNotFoundError(CurrencyConverterError):
    pass


class CannotGetRatesError(CurrencyConverterError):
    def __init__(self, *args):
        super().__init__(*args)
        cause = self.__cause__
        if isinstance(cause, requests.HTTPError):
            self.response_content = cause.response.text


@dataclass
class Currency:
    values: list[float]
    name: str


class CurrencyConverterABC(ABC):
    @abstractmethod
    def convert(self, dst_currency: str, *prices: Currency) -> list[float]:
        pass


class CurrencyConverter(CurrencyConverterABC):
    def __init__(self):
        self._url = "https://open.er-api.com/v6"

    def convert(self, dst_currency: str, *currencies: Currency) -> list[float]:
        try:
            resp = requests.get(url=f"{self._url}/latest/{dst_currency}")

        except (RequestException, ConnectionError, Timeout, HTTPError) as e:
            raise CannotGetRatesError() from e

        rates = resp.json()["conversion_rates"]

        try:
            return [rates[c.name] * c.values for c in currencies]
        except KeyError as e:
            raise CurrencyNotFoundError() from e
