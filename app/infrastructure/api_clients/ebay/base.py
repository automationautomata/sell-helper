import base64
import os

import aiohttp
import requests

from ....data import OAuth2Settings
from ..utils import request_exception_chain
from . import models


class EbayRequestError(Exception):
    @property
    def response_content(self) -> str | None:
        cause = self.__cause__
        if isinstance(cause, requests.HTTPError) and cause.response is not None:
            return cause.response.text


class EbayAuthError(EbayRequestError):
    pass


class EbayClientBase:
    _api_endpoint: str = ""
    application_token: str

    def __init__(self, domain: models.EbayDomain, settings: OAuth2Settings):
        self.settings = settings
        super().__init__(domain)

    def url(self, path: str):
        return f"{self._url_base}{path}"


class EbayUserClient(EbayClientBase):
    @staticmethod
    def _user_auth_header(token: str):
        return {
            "Authorization": f"Bearer {token}",
        }

    async def refresh_token(self, refresh_token: str) -> models.RefreshTokenResponse:
        auth_str = f"{self.settings.client_id}:{self.settings.client_secret}"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {base64.b64encode(auth_str.encode()).decode()}",
        }
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scopes": self.settings.scope,
        }
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    self.settings, data=payload, headers=headers
                ) as resp:
                    data = None
                    if resp.content.total_bytes != 0:
                        data = await resp.json()
                    resp.raise_for_status()
                return models.RefreshTokenResponse.model_validate(data)

            except aiohttp.ClientResponseError as e:
                raise EbayAuthError() from e

            except aiohttp.ClientConnectionError as e:
                raise EbayAuthError() from e


class EbayApplicationClient(EbayClientBase):
    @request_exception_chain(default=EbayAuthError)
    def update_token(self):
        auth_str = f"{self.settings.client_id}:{self.settings.client_secret}"
        response = requests.post(
            url=self.settings.access_token_url,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"{base64.b64encode(auth_str.encode()).decode()}",
            },
            data=dict(
                grant_type="client_credentials",
                scope=self.settings.scope,
            ),
        )

        os.environ["EBAY_APPLICATION_TOKEN"] = response.json()["token"]

    @classmethod
    def _app_auth_header(cls):
        return {
            "Authorization": f"Bearer {os.getenv('EBAY_APPLICATION_TOKEN')}",
        }
