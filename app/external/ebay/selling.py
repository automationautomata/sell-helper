import os

import requests

from ...utils import utils
from . import models
from .base_client import EbayClientBase
from .errors import EbayRequestError


class EbaySellingClientError(EbayRequestError):
    pass


class EbaySellingClient(EbayClientBase):
    API_ENDPOINT = "/sell/inventory/v1"

    @utils.request_exception_chain(default=EbaySellingClientError)
    def create_or_replace_inventory_item(
        self, sku: str, item: models.InventoryItem, lang: str = "en-US"
    ):
        response = requests.put(
            f"{self.url_base}/inventory_item/{sku}",
            headers={
                **self._auth_header(),
                "Content-Type": "application/json",
                "Content-Language": lang,
            },
            json=item.model_dump(by_alias=True, exclude_unset=True),
        )
        response.raise_for_status()
# '{"errors":[{"errorId":25709,"domain":"API_INVENTORY","subdomain":"Selling","category":"Request","message":"Invalid value for header Content-Language."}]}'

    @utils.request_exception_chain(default=EbaySellingClientError)
    def delete_inventory_item(self, sku: int):
        response = requests.delete(
            url=f"{self.url_base}/inventory_item/{sku}",
            headers=self._auth_header(),
            json={"offerId": sku},
        )
        response.raise_for_status()

    @utils.request_exception_chain(default=EbaySellingClientError)
    def create_offer(self, item: models.Offer, lang: str = "en-US") -> int:
        """Creates offer and returnes offer_id"""

        response = requests.post(
            url=f"{self.url_base}/offer",
            json=item.model_dump(by_alias=True, exclude_unset=True),
            headers={
                **self._auth_header(),
                "Content-Type": "application/json",
                "Content-Language": lang,
            },
        )
        response.raise_for_status()
        return response.json()["offerId"]

    @utils.request_exception_chain(default=EbaySellingClientError)
    def publish_offer(self, offer_id: int):
        response = requests.post(
            url=f"{self.url_base}/offer/{offer_id}/publish",
            headers=self._auth_header(),
        )
        response.raise_for_status()

    @utils.request_exception_chain(default=EbaySellingClientError)
    def delete_offer(self, offer_id: int):
        response = requests.delete(
            url=f"{self.url_base}/offer/{offer_id}",
            headers=self._auth_header(),
        )
        response.raise_for_status()
