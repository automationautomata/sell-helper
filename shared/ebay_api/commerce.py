import requests

from ..utils import request_exception_chain
from .base_client import EbayClientBase
from .errors import EbayRequestError
from .models import EbayDomain, ImageResponse

API_ENDPOINT = "/commerce/media/v1_beta"


class CommerceClientError(EbayRequestError):
    pass


class EbayCommerceClient(EbayClientBase):
    def __init__(self, domain: EbayDomain):
        subdomain = ".sandbox" if "sandbox" in domain else ""
        self.URL_BASE = f"https://apim{subdomain}.ebay.com{API_ENDPOINT}"

    @request_exception_chain(default=CommerceClientError)
    def upload_image(self, img_path: str, token: str) -> ImageResponse:
        """Upload image and returnes imageUrl"""

        resp = requests.post(
            url=f"{self.URL_BASE}/image/create_image_from_file",
            headers=self._auth_header(token),
            files={"image": open(img_path, "rb")},
        )
        return ImageResponse.model_validate(resp.json())
