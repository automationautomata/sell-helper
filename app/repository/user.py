import uuid

from sqlalchemy.future import select

from app.domain.entities.user import User

from .base import BaseRepository
from .models import UserModel


class UserRepository(BaseRepository):
    async def get_user_by_email(self, email: str) -> User | None:
        cond = UserModel.email == email and not UserModel.deleted
        q = select(UserModel).filter(cond)

        raw_user = (await self.session.execute(q)).scalar_one_or_none()
        if raw_user is None:
            return

        return User(
            uuid=raw_user.uuid,
            email=raw_user.email,
            password_hash=raw_user.password_hash,
        )

    async def get_user_by_uuid(self, uuid: uuid.UUID) -> User | None:
        cond = UserModel.uuid == uuid and not UserModel.deleted
        q = select(UserModel).filter(cond)

        raw_user = (await self.session.execute(q)).scalar_one_or_none()
        if raw_user is None:
            return

        return User(
            uuid=raw_user.uuid,
            email=raw_user.email,
            password_hash=raw_user.password_hash,
        )

    async def add_user(self, email: str, password_hash: str) -> User:
        new_user = UserModel(email=email, password_hash=password_hash)
        await self.session.add(new_user)
        await self.session.commit()
        await self.session.refresh(new_user)
        return User(
            uuid=new_user.uuid,
            email=new_user.email,
            password_hash=new_user.password_hash,
        )
