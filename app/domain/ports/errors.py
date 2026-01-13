class UserAccountNotAuthorizedError(Exception):
    pass


class AuthError(Exception):
    pass


class UserAuthFailedError(AuthError):
    pass


class CannotCreateUserError(AuthError):
    pass


class UserAlreadyExistsError(AuthError):
    pass


class RegistrationError(Exception):
    pass


class UserAlreadyExists(RegistrationError):
    pass


class SearchServiceError(Exception):
    pass


class ProductCategoriesNotFoundError(SearchServiceError):
    pass


class SellingError(Exception):
    pass


class UserUnauthorisedError(SellingError):
    pass


class UserAuthorizationFailed(SellingError):
    pass


class CategoryNotFound(SellingError):
    pass


class MarketplaceOAuthServiceError(Exception):
    pass


class MarketplaceUnauthorisedError(MarketplaceOAuthServiceError):
    pass
