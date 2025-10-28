from abc import ABC, abstractmethod
from typing import Optional

from sqlalchemy.orm import Session

from ...domain.user import User


class UsersRepositoryABC(ABC):
    @abstractmethod
    def get_user_by_email(self, email: str) -> User:
        pass


class UsersRepository(ABC):
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
