class SearchEngineError(Exception):
    pass


class JWTAuthError(Exception):
    pass


class InvalidTokenError(JWTAuthError):
    pass


class InvalidPayloadTypeError(JWTAuthError):
    pass


class MarketplaceAPIError(Exception):
    pass


class CategoryNotFoundError(MarketplaceAPIError):
    pass


class InvalidValue(MarketplaceAPIError):
    pass


class CategoryPredictorError(Exception):
    pass


class CategoriesNotFoundError(CategoryPredictorError):
    pass


class UserRepositoryError(Exception):
    pass


class UserAlreadyExistsError(UserRepositoryError):
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
