import requests

from ....data import OAuth2Settings
from ..utils import request_exception_chain
from .base import EbayRequestError, EbayUserClient
from .models import EbayDomain, ImageResponse


class EbayCommerceClientError(EbayRequestError):
    pass


class EbayCommerceClient(EbayUserClient):
    _api_endpoint = "/commerce/media/v1_beta"

    def __init__(self, domain: EbayDomain, settings: OAuth2Settings):
        subdomain = ".sandbox" if "sandbox" in domain else ""
        self._url_base = f"https://apim{subdomain}.ebay.com{self._api_endpoint}"
        self.settings = settings

    @request_exception_chain(default=EbayCommerceClientError)
    def upload_image(self, img_path: str, token: str) -> ImageResponse:
        """Upload image and returnes imageUrl"""

        resp = requests.post(
            url=self.url("/image/create_image_from_file"),
            headers=self._user_auth_header(token),
            files={"image": open(img_path, "rb")},
        )
        return ImageResponse.model_validate(resp.json())
