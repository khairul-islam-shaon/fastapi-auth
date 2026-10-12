from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import (
    EmailAlreadyExistsError,
   
    InvalidCredentialsError,
)
from app.core.security import (
    create_access_token,
    hash_password,
    verify_password,
)
from app.db.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
from app.schemas.auth import LoginRequest
from app.schemas.user import UserCreate


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repository = UserRepository(session)

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

    async def login(self, data: LoginRequest) -> str:
        email = str(data.email).strip().lower()

        user = await self.user_repository.get_by_email(email)

        if user is None:
            raise InvalidCredentialsError()

        if not verify_password(
            data.password,
            user.password_hash,
        ):
            raise InvalidCredentialsError()

       

        access_token = create_access_token(
            user_id=str(user.id),
            role=user.role.value,
        )

        return access_token