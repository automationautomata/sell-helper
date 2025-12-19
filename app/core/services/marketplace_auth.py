import uuid

from ..domain.entities.user import User
from ..domain.ports import MarketplaceAuthServiceError
from .ports import (
    AccessTokensStorageError,
    IAccessTokensStorage,
    IMarketplaceOAuth,
    IRefreshTokensStorage,
    IUsersRepository,
    MarketplaceOAuthError,
    RefreshTokensStorageError,
    Token,
    UserRepositoryError,
)


class MarketplaceAuthService:
    def __init__(
        self,
        user_repo: IUsersRepository,
        oauth: IMarketplaceOAuth,
        access_tokens_storage: IAccessTokensStorage,
        refresh_tokens_storage: IRefreshTokensStorage,
    ):
        self._user_repo = user_repo
        self._oauth = oauth
        self._access_tokens_storage = access_tokens_storage
        self._refresh_tokens_storage = refresh_tokens_storage

    async def auth(self, user_data: str, code: str):
        try:
            user = await self._user_repo.get_user_by_uuid(uuid.UUID(user_data))
        except UserRepositoryError as e:
            raise MarketplaceAuthServiceError() from e

        if user is None:
            raise MarketplaceAuthServiceError("User not found")

        try:
            tokens = self._oauth.get_tokens(code)

            access_token = Token(
                tokens=tokens.access_token,
                ttl=tokens.access_token_ttl,
            )
            key = user.uuid.hex
            await self._access_tokens_storage.store(key, access_token)

            refresh_token = Token(
                tokens=tokens.access_token,
                ttl=tokens.access_token_ttl,
            )
            await self._refresh_tokens_storage.store(user.uuid, refresh_token)
        except (
            MarketplaceOAuthError,
            AccessTokensStorageError,
            RefreshTokensStorageError,
        ) as e:
            raise MarketplaceAuthServiceError() from e

    async def logout(self, user_uuid: uuid.UUID):
        try:
            await self._refresh_tokens_storage.remove(user_uuid)
        except RefreshTokensStorageError as e:
            raise MarketplaceAuthServiceError() from e

    async def marketplace_auth_url(self) -> str:
        return self._oauth.generate_auth_url()
