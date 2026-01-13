class Base(Exception):
    pass


class AuthError(Base):
    pass


class InvalidUserToken(AuthError):
    pass


class RegistrationError(Base):
    pass


class CannotCreateUser(RegistrationError):
    pass


class UserAlreadyExists(RegistrationError):
    pass


class SearchServiceError(Base):
    pass


class ProductCategoriesNotFound(SearchServiceError):
    pass


class SellingServiceError(Base):
    pass


class InvalidItemStructure(SellingServiceError):
    pass


class InvalidMarketplaceAspects(InvalidItemStructure):
    pass


class InvalidProductAspects(InvalidItemStructure):
    pass


class MarketplaceAuthorizationFailed(SellingServiceError):
    pass


class UserUnauthorisedInMarketplace(MarketplaceAuthorizationFailed):
    pass


class InvalidCategory(SellingServiceError):
    pass


class MarketplaceOAuthServiceError(Base):
    pass


class InvalidToken(MarketplaceOAuthServiceError):
    pass


class MarketplaceUnauthorised(MarketplaceOAuthServiceError):
    pass
