from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.ports import IUsersRepository
from .user import UsersRepository


class RepositoryProvider(Provider):
    @provide(scope=Scope.APP)
    def user_repository(self, session: AsyncSession) -> IUsersRepository:
        return UsersRepository(session)
