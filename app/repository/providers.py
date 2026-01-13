from dishka import Provider, Scope, provide

from ..services.ports import IRefreshTokenStorage, IUserRepository
from .refresh_tokens import RefreshTokenRepository
from .user import UserRepository


class RepositoryProvider(Provider):
    user_repository = provide(
        UserRepository, provides=IUserRepository, scope=Scope.REQUEST
    )
    refresh_token_storage = provide(
        RefreshTokenRepository, provides=IRefreshTokenStorage, scope=Scope.REQUEST
    )
