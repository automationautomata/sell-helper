from dataclasses import dataclass

from ..domain.entities import MarketplaceAccount
from ..domain.ports import (
    MarketplaceAuthorizationFailed,
    MarketplaceUnauthorised,
)
from .ports import (
    IAccessTokenStorage,
    IMarketplaceOAuthFactory,
    IRefreshTokenStorage,
    MarketplaceOAuthError,
    TokenStorageError,
)


@dataclass
class MarketplaceTokenManager:
    access_token_storage: IAccessTokenStorage
    refresh_token_storage: IRefreshTokenStorage
    oauth_factory: IMarketplaceOAuthFactory
    token_ttl_threshold: int

    async def access_token(self, account: MarketplaceAccount) -> str:
        try:
            access_token = await self.access_token_storage.get(account)
            if (
                access_token is not None
                and access_token.ttl >= self.token_ttl_threshold
            ):
                return access_token.token

        except TokenStorageError:
            pass

        try:
            refresh_token = await self.refresh_token_storage.get(account)
        except TokenStorageError as e:
            raise MarketplaceAuthorizationFailed() from e

        if refresh_token is None:
            raise MarketplaceUnauthorised()

        try:
            oauth = self.oauth_factory.get(account.marketplace)

            access_token = await oauth.new_access_token(refresh_token.token)
            await self.access_token_storage.store(account, access_token.token)

            return access_token.token

        except (MarketplaceOAuthError, TokenStorageError) as e:
            raise MarketplaceAuthorizationFailed() from e
