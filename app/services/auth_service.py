from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import EmailAlreadyExistsError
from app.core.security import hash_password
from app.db.models.user import User, UserRole
from app.repositories.user_repository import UserRepository
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