from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select

from app.domain.entities import MarketplaceAccount
from app.services.ports import (
    AuthToken,
    RefreshTokenStorageError,
    TokenExpiredError,
)

from .base import BaseRepository
from .models import RefreshToken


class RefreshTokenRepository(BaseRepository):
    async def store(self, token: AuthToken, account: MarketplaceAccount):
        expires_at = datetime.now(tz=UTC) + timedelta(seconds=token.ttl)

        row = RefreshToken(
            user_uuid=account.user_uuid,
            marketplace=account.marketplace,
            refresh_token=token.token,
            expires_at=expires_at,
        )

        try:
            self.session.add(row)
            await self.session.commit()
        except Exception as e:
            raise RefreshTokenStorageError() from e

    async def get(self, account: MarketplaceAccount) -> AuthToken | None:
        q = (
            select(RefreshToken)
            .where(
                RefreshToken.user_uuid == account.user_uuid
                and RefreshToken.marketplace == account.marketplace
            )
            .order_by(RefreshToken.created_at.desc())
            .limit(1)
        )

        try:
            row = (await self.session.execute(q)).scalar_one_or_none()
        except Exception as e:
            raise RefreshTokenStorageError() from e

        if not row:
            return

        now = datetime.now(tz=UTC)
        ttl = int((row.expires_at - now).total_seconds())
        if ttl < 0:
            raise TokenExpiredError("token for user")

        return AuthToken(token=row.refresh_token, ttl=ttl)

    async def delete(self, account: MarketplaceAccount):
        subquery = (
            select(RefreshToken.id)
            .where(
                RefreshToken.user_uuid == account.user_uuid
                and RefreshToken.marketplace == account.marketplace
            )
            .order_by(RefreshToken.created_at.desc())
            .limit(1)
            .scalar_subquery()
        )

        stmt = delete(RefreshToken).where(RefreshToken.id == subquery)
        try:
            await self.session.execute(stmt)
            await self.session.commit()
        except Exception as e:
            raise RefreshTokenStorageError() from e
