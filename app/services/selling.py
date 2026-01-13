from dataclasses import asdict, dataclass

from ..domain.dto import ItemDTO, MarketplaceAccountDTO
from ..domain.entities import (
    AspectValue,
    Item,
    MarketplaceAccount,
    ProductStructure,
)
from ..domain.entities.errors import AspectsValidationError
from ..domain.ports import (
    CategoryNotFound,
    SellingError,
    UserAuthorizationFailed,
    UserUnauthorisedError,
)
from .mapping import FromDTO
from .ports import (
    CategoryNotFoundError,
    IAccessTokenStorage,
    IMarketplaceAPIFactory,
    IMarketplaceAspectsFactory,
    IMarketplaceOAuthFactory,
    IRefreshTokenStorage,
    MarketplaceAPIError,
    MarketplaceOAuthError,
    RefreshTokenStorageError,
    TokenStorageError,
)


@dataclass
class SellingService:
    api_factory: IMarketplaceAPIFactory
    access_token_storage: IAccessTokenStorage
    refresh_token_storage: IRefreshTokenStorage
    oauth_factory: IMarketplaceOAuthFactory
    token_ttl_threshold: int
    type_factory: IMarketplaceAspectsFactory

    async def publish(
        self, item_data: ItemDTO, account: MarketplaceAccountDTO, *images: str
    ):
        markeplace_aspects_type = self.type_factory.get(account.marketplace)
        marketplace_aspects = markeplace_aspects_type.validate(
            item_data.marketplace_aspects_data
        )
        product_aspects = self._validate_product_structure(
            item_data.category, item_data.product_aspects
        )

        item = Item(
            **asdict(item),
            marketplace_aspects=marketplace_aspects,
            product_aspects=product_aspects,
        )
        token = await self._access_token(FromDTO.account(account))

        try:
            marketplace_api = self.api_factory.get(marketplace_api)
            marketplace_api.publish(item, token, *images)

        except MarketplaceAPIError as e:
            raise CategoryNotFound() from e

    def _validate_product_structure(
        self, category_name: str, aspects_data: dict[str], marketplace: str
    ) -> list[AspectValue]:
        try:
            marketplace_api = self.api_factory.get(marketplace)
            fields = marketplace_api.get_product_aspects(category_name)

            product_structure = ProductStructure(fields=fields)
            return product_structure.validate(aspects_data)
        except (
            MarketplaceAPIError,
            CategoryNotFoundError,
            AspectsValidationError,
        ) as e:
            raise SellingError() from e

    async def _access_token(self, account: MarketplaceAccount) -> str:
        try:
            access_token = await self.access_token_storage.get(account)
        except TokenStorageError as e:
            pass

        if access_token is not None and access_token.ttl < self.token_ttl_threshold:
            return access_token.token

        try:
            refresh_token = await self.refresh_token_storage.get(account)
        except TokenStorageError as e:
            raise UserAuthorizationFailed()

        if refresh_token is None:
            raise UserUnauthorisedError()

        try:
            oauth = self.oauth_factory.get(account.marketplace)
            access_token = await oauth.new_access_token(refresh_token.token)
            await self.access_token_storage.store(account, access_token.token)

            return access_token.token
        except (MarketplaceOAuthError, TokenStorageError) as e:
            raise UserAuthorizationFailed() from e
