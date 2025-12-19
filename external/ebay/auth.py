import base64
from urllib import parse

import requests
from authlib.integrations.requests_client import OAuth2Session

from ..utils import request_exception_chain
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
    def __init__(
        self, appid: str, certid: str, redirect_uri: str, domain: models.EbayDomain
    ):
        self._appid = appid
        self._certid = certid
        self._redirect_uri = redirect_uri
        self._url_base = f"https://{domain}"

    @request_exception_chain(default=EbayAuthError)
    async def update_token(self, refresh_token: str) -> models.RefreshTokenResponse:
        auth_str = f"{self._appid}:{self._certid}"
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {base64.b64encode(auth_str.encode()).decode()}",
        }
        body = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "scopes": SCOPES,
        }
        url = f"{self._url_base}{API_ENDPOINT}"

        resp = requests.post(url, data=body, headers=headers)
        resp.raise_for_status()
        return models.RefreshTokenResponse.model_validate(resp.json())

    def application_access_token(self) -> str:
        try:
            client = OAuth2Session(
                client_id=self._appid,
                client_secret=self._certid,
                scope=SCOPES,
            )

            token = client.fetch_token(
                url=f"{self._url_base}{API_ENDPOINT}",
                grant_type="client_credentials",
            )
        except Exception as e:
            raise EbayAuthError() from e

        return token

    def authorization_url(self) -> str:
        param = {
            "client_id": self._appid,
            "redirect_uri": self._redirect_uri,
            "response_type": "code",
            "prompt": "login",
            "scope": " ".join(SCOPES),
        }

        return f"{self._url_base}?{parse.urlencode(param)}"

    @request_exception_chain(default=EbayAuthError)
    def tokens_by_authorization_code(
        self, raw_code: str, state: str = ""
    ) -> models.GetTokenResponse:
        code = parse.unquote(raw_code)
        auth_str = f"{self._appid}:{self._certid}"

        resp = requests.post(
            url=f"{self._url_base}{API_ENDPOINT}",
            data={
                "grant_type": "authorization_code",
                "redirect_uri": self._redirect_uri,
                "code": code,
                "state": state,
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {base64.b64encode(auth_str.encode()).decode()}",
            },
        )
        resp.raise_for_status()
        return models.GetTokenResponse.model_validate(resp.json())
