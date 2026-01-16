from dataclasses import asdict, dataclass

from ..domain.dto import ItemDTO, MarketplaceAccountDTO
from ..domain.entities import AspectValue, Item, ProductStructure
from ..domain.entities.errors import AspectsValidationError
from ..domain.ports import (
    InvalidCategory,
    InvalidMarketplaceAspects,
    InvalidProductAspects,
    MarketplaceAuthorizationFailed,
    SellingServiceError,
)
from .common import MarketplaceTokenManager
from .mapping import FromDTO
from .ports import (
    AccountSettingsNotFound,
    CategoryNotFound,
    IMarketplaceAPIFactory,
    IMarketplaceAspectsFactory,
    MarketplaceAPIError,
)


@dataclass
class SellingService:
    api_factory: IMarketplaceAPIFactory
    token_manager: MarketplaceTokenManager
    type_factory: IMarketplaceAspectsFactory

    async def publish(self, dto: ItemDTO, account: MarketplaceAccountDTO, *images: str):
        item_data = asdict(dto)
        markeplace_aspects_type = self.type_factory.get(account.marketplace)
        marketplace_aspects = markeplace_aspects_type.validate(
            item_data.pop("marketplace_aspects_data")
        )
        if marketplace_aspects is None:
            raise InvalidMarketplaceAspects()

        product_aspects = self._validate_product_structure(
            item_data["category"],
            item_data.pop("product_aspects"),
            marketplace=account.marketplace,
        )
        try:
            item = Item(
                **item_data,
                marketplace_aspects=marketplace_aspects,
                product_aspects=product_aspects,
            )

            token = await self.token_manager.access_token(FromDTO.account(account))

            marketplace_api = self.api_factory.get(account.marketplace)
            marketplace_api.publish(item, token, *images)

        except AccountSettingsNotFound as e:
            raise InvalidMarketplaceAspects() from e
        except MarketplaceAPIError as e:
            raise SellingServiceError() from e
        except MarketplaceAuthorizationFailed:
            raise

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
            CategoryNotFound,
            AspectsValidationError,
        ) as e:
            error_mapping = {
                MarketplaceAPIError: SellingServiceError(),
                CategoryNotFound: InvalidCategory(),
                AspectsValidationError: InvalidProductAspects(),
            }
            raise error_mapping[type(e)] from e
