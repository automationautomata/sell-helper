import os

import requests

from .utils import utils


class BarcodeSearchError(Exception):
    pass


@utils.request_exception_chain(default=BarcodeSearchError)
def search(barcode: str, token: str) -> str:
    """Search product by the barcode and returns it's name"""

    resp = requests.get(
        url="https://api.barcodespider.com/v1/lookup",
        headers={"token": token},
        params={"upc": barcode},
    )
    resp.raise_for_status()
    return resp.json()["item_attributes"]["title"]
