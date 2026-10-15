from datetime import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> RefreshToken:
        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )

        self.session.add(refresh_token)

        await self.session.flush()
        await self.session.refresh(refresh_token)

        return refresh_token

    async def get_by_hash(
        self,
        token_hash: str,
    ) -> RefreshToken | None:
        result = await self.session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash
            )
        )

        return result.scalar_one_or_none()

    async def revoke(
        self,
        refresh_token: RefreshToken,
        revoked_at: datetime,
    ) -> RefreshToken:
        refresh_token.revoked_at = revoked_at

        await self.session.flush()
        await self.session.refresh(refresh_token)

        return refresh_token