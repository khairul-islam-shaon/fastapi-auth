from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
)
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)
from app.db.models.user import User, UserRole
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repository = UserRepository(session)
        self.refresh_token_repository = RefreshTokenRepository(session)

    async def register(self, data: UserCreate) -> User:
        email = str(data.email).strip().lower()

        existing_user = await self.user_repository.get_by_email(email)

        if existing_user:
            raise EmailAlreadyExistsError()

        user = User(
            email=email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            role=UserRole.USER,
        )

        try:
            user = await self.user_repository.create(user)
            await self.session.commit()
        except IntegrityError:
            await self.session.rollback()
            raise EmailAlreadyExistsError()

        return user

    async def login(
        self,
        data: LoginRequest,
    ) -> tuple[str, str]:
        email = str(data.email).strip().lower()

        user = await self.user_repository.get_by_email(email)

        if user is None:
            raise InvalidCredentialsError()

        if not verify_password(
            data.password,
            user.password_hash,
        ):
            raise InvalidCredentialsError()

        # Same error as bad credentials so account status is not revealed.
        if not user.is_active:
            raise InvalidCredentialsError()

        access_token = create_access_token(
            user_id=str(user.id),
            role=user.role.value,
        )

        refresh_token, expires_at = create_refresh_token(
            user_id=str(user.id),
        )

        refresh_token_hash = hash_refresh_token(
            refresh_token
        )

        await self.refresh_token_repository.create(
            user_id=user.id,
            token_hash=refresh_token_hash,
            expires_at=expires_at,
        )

        await self.session.commit()

        return access_token, refresh_token