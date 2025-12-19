import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..domain.entities.user import User
from .models import UserModel


class UsersRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_by_email(self, email: str) -> Optional[User]:
        q = select(UserModel).filter(
            UserModel.email == email and UserModel.deleted == False
        )
        raw_user = (await self.db.execute(q)).scalars().first()
        if raw_user is None:
            return

        return User(
            email=raw_user.email,
            password_hash=raw_user.password_hash,
        )

    async def get_user_by_uuid(self, uuid: uuid.UUID) -> Optional[User]:
        q = select(UserModel).filter(
            UserModel.uuid == uuid and UserModel.deleted == False
        )
        raw_user = (await self.db.execute(q)).scalars().first()
        if raw_user is None:
            return

        return User(
            uuid=raw_user.uuid,
            email=raw_user.email,
            password_hash=raw_user.password_hash,
        )

    async def add_user(self, email: str, password_hash: str) -> User:
        new_user = UserModel(email=email, password_hash=password_hash)
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return User(
            uuid=new_user.uuid,
            email=new_user.email,
            password_hash=new_user.password_hash,
        )
