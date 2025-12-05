import base64
import os
from typing import Optional

import aiohttp

from ...config import EbayConfig
from ...data import EnvKeys
from . import models
from .errors import EbayRequestError

API_ENDPOINT = "/identity/v1/oauth2/token"

SCOPES = (
    "https://api.ebay.com/oauth/api_scope",
    "https://api.ebay.com/oauth/api_scope/sell.account",
    "https://api.ebay.com/oauth/api_scope/sell.inventory",
)


class EbayAuthError(EbayRequestError):
    pass


class EbayAuthClient:
    def __init__(self, config: EbayConfig):
        self._config = config
        self.url_base = f"https://{self._config.domain}"

    async def get_token(self) -> Optional[models.RefreshTokenResponse]:
        url = f"{self.url_base}{API_ENDPOINT}"

        auth_str = f"{self._config.appid}:{self._config.certid}"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {base64.b64encode(auth_str.encode()).decode()}",
        }
        payload = {
            "grant_type": "refresh_token",
            "refresh_token": os.getenv(EnvKeys.EBAY_REFRESH_TOKEN),
            "scopes": SCOPES,
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, data=payload, headers=headers) as resp:
                    resp.raise_for_status()
                    if resp.content.total_bytes == 0:
                        return
                    data = await resp.json()
                    return models.RefreshTokenResponse.model_validate(data)

            except (aiohttp.ClientResponseError, aiohttp.ClientConnectionError) as e:
                raise EbayAuthError() from e
