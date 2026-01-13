import requests

from ..utils import request_exception_chain
from . import models
from .base import EbayRequestError, EbayUserClient


class EbaySellingClientError(EbayRequestError):
    pass


class EbaySellingClient(EbayUserClient):
    _api_endpoint = "/sell/inventory/v1"

    @request_exception_chain(default=EbaySellingClientError)
    def create_or_replace_inventory_item(
        self, sku: str, item: models.InventoryItem, token: str, lang: str = "en-US"
    ):
        response = requests.put(
            url=self.url(f"/inventory_item/{sku}"),
            headers={
                **self._user_auth_header(token),
                "Accept-Language": lang,
            },
            json=item.model_dump(by_alias=True, exclude_unset=True),
        )
        response.raise_for_status()

    @request_exception_chain(default=EbaySellingClientError)
    def delete_inventory_item(self, sku: int, token: str):
        response = requests.delete(
            url=self.url(f"/inventory_item/{sku}"),
            headers=self._user_auth_header(token),
            json={"offerId": sku},
        )
        response.raise_for_status()

    @request_exception_chain(default=EbaySellingClientError)
    def create_offer(self, item: models.Offer, token: str, lang: str = "en-US") -> int:
        """Creates offer and returnes offer_id"""

        response = requests.post(
            url=self.url("/offer"),
            json=item.model_dump(by_alias=True, exclude_unset=True),
            headers={
                **self._user_auth_header(token),
                "Content-Type": "application/json",
                "Content-Language": lang,
            },
        )
        response.raise_for_status()
        return response.json()["offerId"]

    @request_exception_chain(default=EbaySellingClientError)
    def publish_offer(self, offer_id: int, token: str):
        response = requests.post(
            url=self.url(f"/offer/{offer_id}/publish"),
            headers=self._user_auth_header(token),
        )
        response.raise_for_status()

    @request_exception_chain(default=EbaySellingClientError)
    def delete_offer(self, offer_id: int, token: str):
        response = requests.delete(
            url=self.url(f"/offer/{offer_id}"),
            headers=self._user_auth_header(token),
        )
        response.raise_for_status()
