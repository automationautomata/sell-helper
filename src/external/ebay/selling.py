import os

import requests
from config import EbayDomain
from data import EnvKeys
from utils import utils

from . import models

API_ENDPOINT = "/sell/inventory/v1"


class EbaySellingClientError(Exception):
    pass


class EbaySellingClient:
    def __init__(self, domain: EbayDomain):  # type: ignore
        self._url_base = f"https://{domain}{API_ENDPOINT}"

    @utils.request_exception_chain(default=EbaySellingClientError)
    def create_or_replace_inventory_item(
        self, sku: str, item: models.InventoryItem, lang: str = "en-US"
    ):
        response = requests.put(
            f"{self._url_base}/inventory_item/{sku}",
            headers={
                "Authorization": f"Bearer {os.getenv(EnvKeys.EBAY_USER_TOKEN)}",
            },
            json=item.model_dump(by_alias=True, exclude_unset=True)
        )
        response.raise_for_status()

    @utils.request_exception_chain(default=EbaySellingClientError)
    def delete_inventory_item(self, sku: int):
        response = requests.delete(
            url=f"{self._url_base}/inventory_item/{sku}",
            headers={
                "Authorization": f"Bearer {os.getenv(EnvKeys.EBAY_USER_TOKEN)}",
            },
            json={"offerId": sku},
        )
        response.raise_for_status()
        return response.json()

    @utils.request_exception_chain(default=EbaySellingClientError)
    def create_offer(self, item: models.Offer, lang: str = "en-US") -> int:
        """Creates offer and returnes offer_id"""
        headers = {
            "Authorization": f"Bearer {os.getenv(EnvKeys.EBAY_USER_TOKEN)}",
            "Content-Type": "application/json",
            "Content-Language": lang,
        }

        response = requests.post(
            url=f"{self._url_base}/offer",
            json=item.model_dump(by_alias=True, exclude_unset=True),
            headers=headers,
        )
        response.raise_for_status()
        return response.json()["offerId"]

    @utils.request_exception_chain(default=EbaySellingClientError)
    def publish_offer(self, offer_id: int):
        response = requests.post(
            url=f"{self._url_base}/offer/{offer_id}/publish",
            headers={
                "Authorization": f"Bearer {os.getenv(EnvKeys.EBAY_USER_TOKEN)}",
            },
        )
        response.raise_for_status()
        return response.json()

    @utils.request_exception_chain(default=EbaySellingClientError)
    def delete_offer(self, offer_id: int):
        response = requests.delete(
            url=f"{self._url_base}/offer/{offer_id}",
            headers={
                "Authorization": f"Bearer {os.getenv(EnvKeys.EBAY_USER_TOKEN)}",
            },
        )
        response.raise_for_status()
        return response.json()
