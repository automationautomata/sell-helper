from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, String
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, registry

mapper_registry = registry()


@mapper_registry.mapped
class UserModel:
    __tablename__ = "users"
    uuid: Mapped[UUID] = mapped_column(PGUUID, primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, default="CURRENT_TIMESTAMP"
    )
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default="FALSE")
