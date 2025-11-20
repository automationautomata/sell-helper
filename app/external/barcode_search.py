import os

import requests
from app.data import EnvKeys
from app.utils import utils


class BarcodeSearchError(Exception):
    pass


@utils.request_exception_chain(default=BarcodeSearchError)
def search(barcode: str) -> str:
    """Search product by the barcode and returns it's name"""
    url = "https://api.barcodespider.com/v1/lookup"
    headers = {
        "token": os.getenv(EnvKeys.BARCODE_SEARCH_TOKEN),
    }
    resp = requests.get(url, headers=headers, params={"upc": barcode})
    resp.raise_for_status()
    return resp.json()["item_attributes"]["title"]
