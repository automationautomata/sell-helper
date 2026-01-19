from dataclasses import dataclass
from datetime import timedelta

from ..services.ports import (
    AuthToken,
    MarketplaceOAuthError,
    OAuth2Tokens,
    OAuthParsingError,
)
from .api_clients.ebay import EbayAuthError, EbayUserClient


@dataclass
class EbayOAuth:
    client: EbayUserClient
    refresh_token_ttl: int = timedelta(weeks=4 * 18).total_seconds()

    async def new_access_token(self, refresh_token: str) -> AuthToken:
        try:
            token = await self.client.refresh_token(refresh_token=refresh_token)
            return AuthToken(
                token=token.access_token,
                ttl=token.expires_in,
            )
        except EbayAuthError as e:
            raise MarketplaceOAuthError() from e

    def parse(self, data: dict[str]) -> OAuth2Tokens:
        try:
            return OAuth2Tokens(
                access_token=AuthToken(
                    token=data["access_token"],
                    ttl=int(data["expiers_in"]),
                ),
                refresh_token=AuthToken(
                    token=data["refresh_token"],
                    ttl=data.get("refresh_token_expires_in", self.refresh_token_ttl),
                ),
            )
        except KeyError as e:
            raise OAuthParsingError() from e
