from ..domain.dto import (
    AccountSettingsDTO,
    AspectValueDTO,
    MarketplaceAccountDTO,
    ProductDTO,
)
from ..domain.entities import MarketplaceAccount, Product
from ..domain.entities.account import AccountSettings


class FromDTO:
    @staticmethod
    def account(dto: MarketplaceAccountDTO) -> MarketplaceAccount:
        return MarketplaceAccount(user_uuid=dto.user_uuid, marketplace=dto.marketplace)


class FromEntity:
    @staticmethod
    def product_dto(product: Product) -> ProductDTO:
        aspectDtos = []
        for a in product.aspects:
            aspectDtos.append(
                AspectValueDTO(name=a.name, value=a.value, is_required=a.is_required)
            )

        return ProductDTO(aspects=aspectDtos, metadata=product.metadata.asdict())

    @staticmethod
    def account_settings(account_settings: AccountSettings) -> AccountSettingsDTO:
        return account_settings.settings
