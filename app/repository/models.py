from datetime import datetime
from uuid import UUID

from sqlalchemy import TIMESTAMP, VARCHAR, Boolean, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, registry

mapper_registry = registry()


@mapper_registry.mapped
class UserModel:
    __tablename__ = "users"
    uuid: Mapped[UUID] = mapped_column(PGUUID, primary_key=True)
    email: Mapped[str] = mapped_column(VARCHAR, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, nullable=False, default="CURRENT_TIMESTAMP"
    )
    deleted: Mapped[bool] = mapped_column(Boolean, nullable=False, default="FALSE")


@mapper_registry.mapped
class RefreshToken:
    __tablename__ = "refresh_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_uuid: Mapped[UUID] = mapped_column(
        ForeignKey("users.uuid"), nullable=False, index=True
    )
    refresh_token: Mapped[str] = mapped_column(Text, nullable=False)
    marketplace: Mapped[str] = mapped_column(VARCHAR, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), nullable=False
    )
