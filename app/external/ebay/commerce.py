import os

import requests

from ...config import EbayDomain
from ...data import EnvKeys
from ...utils import utils
from ..ebay.errors import EbayRequestError
from .base_client import EbayClientBase
from .models import UploadImageResponse


class CommerceClientError(EbayRequestError):
    pass


class EbayCommerceClient(EbayClientBase):
    API_ENDPOINT = "/commerce/media/v1_beta"

    def __init__(self, domain: EbayDomain):  # type: ignore
        subdomain = ".sandbox" if "sandbox" in domain else ""
        self._url_base = f"https://apim{subdomain}.ebay.com{self.API_ENDPOINT}"

    @property
    def url_base(self):
        return self._url_base

    @utils.request_exception_chain(default=CommerceClientError)
    def upload_image(self, img_path: str) -> UploadImageResponse:
        """Upload image and returnes imageUrl"""
        url = f"{self.url_base}/image/create_image_from_file"

        files = {"image": open(img_path, "rb")}
        response = requests.post(url, headers=self._auth_header(), files=files)
        return UploadImageResponse.model_validate(response.json())
