import uuid
from dataclasses import dataclass

from ..domain.dto import MarketplaceAccountDTO
from ..domain.ports import (
    InvalidToken,
    MarketplaceOAuthServiceError,
    MarketplaceUnauthorised,
)
from .mapping import FromDTO
from .ports import (
    IAccessTokenStorage,
    IJWTAuth,
    IMarketplaceOAuthFactory,
    IRefreshTokenStorage,
    IUserRepository,
    OAuthParsingError,
    TokenNotFoundError,
    TokenStorageError,
)


class OAuthPayload:
    user_uuid: uuid.UUID


@dataclass
class MarketplaceOAuthService:
    user_repo: IUserRepository
    jwt_auth: IJWTAuth[OAuthPayload]
    access_tokens_storage: IAccessTokenStorage
    refresh_tokens_storage: IRefreshTokenStorage
    oauth_factory: IMarketplaceOAuthFactory

    def generate_token(self, user_uuid: uuid.UUID) -> str:
        jwt_token = self.jwt_auth.generate_token(OAuthPayload(user_uuid=user_uuid))
        return jwt_token.token

    async def save_tokens(
        self, user_token: str, oauth_tokens: dict[str], marketplace: str
    ) -> uuid.UUID:
        try:
            payload = self.jwt_auth.verify_token(user_token, OAuthPayload)
            if payload is None:
                raise InvalidToken()
            oauth = self.oauth_factory.get(marketplace)

            tokens = oauth.parse(oauth_tokens)
            await self.access_tokens_storage.store(tokens.access_token)
            await self.refresh_tokens_storage.store(tokens.refresh_token)

            return payload.user_uuid

        except (TokenStorageError, OAuthParsingError) as e:
            raise MarketplaceOAuthServiceError() from e

    async def logout(self, account: MarketplaceAccountDTO):
        try:
            entity = FromDTO.account(account)
            await self.access_tokens_storage.delete(entity)
            await self.refresh_tokens_storage.delete(entity)

        except TokenNotFoundError as e:
            raise MarketplaceUnauthorised() from e
        except TokenStorageError as e:
            raise MarketplaceOAuthServiceError() from e
