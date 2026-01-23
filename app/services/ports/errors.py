class SearchEngineError(Exception):
    pass


class JWTAuthError(Exception):
    pass


class InvalidPayloadTypeError(JWTAuthError):
    pass


class MarketplaceAPIError(Exception):
    pass


class AccountSettingsNotFound(Exception):
    pass


class CategoryNotFound(MarketplaceAPIError):
    pass


class InvalidValue(MarketplaceAPIError):
    pass


class CategoryPredictorError(Exception):
    pass


class CategoriesNotFoundError(CategoryPredictorError):
    pass


class UserRepositoryError(Exception):
    pass


class UserAlreadyExists(UserRepositoryError):
    pass


class TokenStorageError(Exception):
    pass


class TokenNotFoundError(TokenStorageError):
    pass


class TokenExpiredError(TokenStorageError):
    pass


class RefreshTokenStorageError(TokenStorageError):
    pass


class AcessTokenStorageError(TokenStorageError):
    pass


class MarketplaceOAuthError(Exception):
    pass


class OAuthParsingError(Exception):
    pass
