from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ...domain.user import User
from .models import UserModel


class UsersRepositoryABC(ABC):
    @abstractmethod
    async def get_user_by_email(self, email: str) -> Optional[User]:
        pass


class UsersRepository(UsersRepositoryABC):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> Optional[User]:
        q = select(UserModel).filter(UserModel.email == email)
        raw_user = (await self.db.execute(q)).scalars().first()
        if raw_user is None:
            return

        return User(
            email=raw_user.email,
            password_hash=raw_user.password_hash,
        )
