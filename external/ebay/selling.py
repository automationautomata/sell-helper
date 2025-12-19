import requests

from ..utils import request_exception_chain
from . import models
from .base_client import EbayClientBase
from .errors import EbayRequestError

API_ENDPOINT = "/sell/inventory/v1"


class EbaySellingClientError(EbayRequestError):
    pass


class EbaySellingClient(EbayClientBase):
    @request_exception_chain(default=EbaySellingClientError)
    def create_or_replace_inventory_item(
        self, sku: str, item: models.InventoryItem, token: str, lang: str = "en-US"
    ):
        response = requests.put(
            f"{self._url_base}/inventory_item/{sku}",
            headers={
                **self._auth_header(token),
                "Accept-Language": lang,
            },
            json=item.model_dump(by_alias=True, exclude_unset=True),
        )
        response.raise_for_status()

    @request_exception_chain(default=EbaySellingClientError)
    def delete_inventory_item(self, sku: int, token: str):
        response = requests.delete(
            url=f"{self._url_base}/inventory_item/{sku}",
            headers=self._auth_header(token),
            json={"offerId": sku},
        )
        response.raise_for_status()

    @request_exception_chain(default=EbaySellingClientError)
    def create_offer(self, item: models.Offer, token: str, lang: str = "en-US") -> int:
        """Creates offer and returnes offer_id"""

        response = requests.post(
            url=f"{self._url_base}/offer",
            json=item.model_dump(by_alias=True, exclude_unset=True),
            headers={
                **self._auth_header(token),
                "Content-Type": "application/json",
                "Content-Language": lang,
            },
        )
        response.raise_for_status()
        return response.json()["offerId"]

    @request_exception_chain(default=EbaySellingClientError)
    def publish_offer(self, offer_id: int, token: str):
        response = requests.post(
            url=f"{self._url_base}/offer/{offer_id}/publish",
            headers=self._auth_header(token),
        )
        response.raise_for_status()

    @request_exception_chain(default=EbaySellingClientError)
    def delete_offer(self, offer_id: int, token: str):
        response = requests.delete(
            url=f"{self._url_base}/offer/{offer_id}",
            headers=self._auth_header(token),
        )
        response.raise_for_status()
