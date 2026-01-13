import uuid
from typing import Protocol

from .. import dto


class IAuthService(Protocol):
    async def verify_user(self, email: str, password: str) -> dto.Token:
        pass

    async def validate(token: str) -> uuid.UUID:
        pass


class IRegistrationService(Protocol):
    async def add_user(self, email: str, password: str) -> dto.Token:
        pass


class ISearchService(Protocol):
    def aspects(
        self,
        product_name: str,
        category_name: str,
        comment: str,
        marketplace: str,
        **settings: dict,
    ) -> dto.ProductDTO:
        """Search product by name and category"""
        pass

    def recognize_product(
        self, img_path: str, marketplace, **settings: dict
    ) -> dto.ProductCategoriesDTO:
        """Search categories by product name"""
        pass


class ISellingService(Protocol):
    async def publish(
        self, item_data: dto.ItemDTO, account: dto.MarketplaceAccountDTO, *images: str
    ) -> None:
        pass


class IMarketplaceOAuthService(Protocol):
    def generate_token(self, user_uuid: uuid.UUID) -> str:
        """
        Generate token for oauth state
        """
        pass

    async def save_tokens(
        self, user_token: str, oauth_tokens: dict[str], marketplace: str
    ) -> uuid.UUID:
        pass

    async def logout(self, account: dto.MarketplaceAccountDTO):
        pass
