from app.domain.dto import AspectValueDTO, MarketplaceAccountDTO, ProductDTO
from app.domain.entities import MarketplaceAccount, Product


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
