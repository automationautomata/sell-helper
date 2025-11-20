import os

import requests

from ..ebay.errors import EbayRequestError

from ...config import EbayDomain
from ...data import EnvKeys
from ...utils import utils
from .models import ImageResponse

API_ENDPOINT = "/commerce/media/v1_beta"


class CommerceClientError(EbayRequestError):
    def __init__(self) -> None:
        cause = self.__cause__
        if isinstance(cause, requests.HTTPError):
            self.response_content = cause.response.text


class EbayCommerceClient:
    def __init__(self, domain: EbayDomain):  # type: ignore
        subdomain = ".sandbox" if "sandbox" in domain else ""
        self.URL_BASE = f"https://apim{subdomain}.ebay.com{API_ENDPOINT}"

    @utils.request_exception_chain(default=CommerceClientError)
    def upload_image(self, img_path: str) -> ImageResponse:
        """Upload image and returnes imageUrl"""
        url = f"{self.URL_BASE}/image/create_image_from_file"
        headers = {
            "Authorization": f"Bearer {os.getenv(EnvKeys.EBAY_USER_TOKEN)}",
        }

        files = {"image": open(img_path, "rb")}
        response = requests.post(url, headers=headers, files=files)
        return ImageResponse.model_validate(response.json())
