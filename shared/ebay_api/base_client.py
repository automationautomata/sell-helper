import os

from .models import EbayDomain


class EbayClientBase:
    API_ENDPOINT: str

    def __init__(self, domain: EbayDomain):
        self._url_base = f"https://{domain}{self.API_ENDPOINT}"

    @staticmethod
    def _auth_header():
        return {
            "Authorization": f"Bearer {os.getenv(EnvKeys.EBAY_USER_TOKEN)}",
        }

    @property
    def url_base(self):
        return self._url_base
