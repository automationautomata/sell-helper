from dataclasses import dataclass

from ..domain.dto import AccountSettingsDTO, MarketplaceAccountDTO
from ..domain.ports import (
    MarketplaceAccountServiceError,
    MarketplaceAuthorizationFailed,
)
from .common import MarketplaceTokenManager
from .mapping import FromDTO, FromEntity
from .ports import IMarketplaceAPIFactory, MarketplaceAPIError


@dataclass
class MarketplaceAccountService:
    token_manager: MarketplaceTokenManager
    api_factory: IMarketplaceAPIFactory

    async def find_settings(self, account: MarketplaceAccountDTO) -> AccountSettingsDTO:
        entity = FromDTO.account(account)
        api = self.api_factory.get(entity.marketplace)

        try:
            token = await self.token_manager.access_token(entity.marketplace)
            account_settings = api.get_account_settings(token)
            return FromEntity.account_settings(account_settings)

        except MarketplaceAPIError as e:
            raise MarketplaceAccountServiceError() from e
        except MarketplaceAuthorizationFailed:
            raise
