***Login service***-এর দায়িত্ব:
email + password
      ↓
UserRepository.get_by_email()
      ↓
User exists?
      ↓
Password verify
      ↓
is_active?
      ↓
JWT access token

1. দুইটা custom exception add করবো
কেন? Service layer যেন HTTPException-এর উপর depend না করে।
app/core/exceptions.py-এ existing EmailAlreadyExistsError রেখে add করো:
class EmailAlreadyExistsError(Exception):    """Raised when a user tries to register with an existing email."""    passclass InvalidCredentialsError(Exception):    """Raised when email or password is invalid."""    passclass InactiveUserError(Exception):    """Raised when a disabled user tries to login."""    pass


InvalidCredentialsError-এ email আর password—দুটোর জন্য same error রাখছি। Security reason: attacker যেন বুঝতে না পারে কোন email system-এ registered।


2. ***AuthService***-এ login method add করো
app/services/auth_service.py:
from sqlalchemy.exc import IntegrityErrorfrom sqlalchemy.ext.asyncio import AsyncSessionfrom app.core.exceptions import (    EmailAlreadyExistsError,    InactiveUserError,    InvalidCredentialsError,)from app.core.security import (    create_access_token,    hash_password,    verify_password,)from app.db.models.user import User, UserRolefrom app.repositories.user_repository import UserRepositoryfrom app.schemas.auth import LoginRequestfrom app.schemas.user import UserCreateclass AuthService:    def __init__(self, session: AsyncSession):        self.session = session        self.user_repository = UserRepository(session)    async def register(self, data: UserCreate) -> User:        email = str(data.email).strip().lower()        existing_user = await self.user_repository.get_by_email(email)        if existing_user:            raise EmailAlreadyExistsError()        user = User(            email=email,            password_hash=hash_password(data.password),            full_name=data.full_name,            role=UserRole.USER,        )        try:            user = await self.user_repository.create(user)            await self.session.commit()        except IntegrityError:            await self.session.rollback()            raise EmailAlreadyExistsError()        return user    async def login(self, data: LoginRequest) -> str:


কেন user.role.value?
Database/model-এ:
UserRole.USER


একটা Enum object।
JWT-তে আমরা clean string চাই:
{
  "role": "USER"
}

তাই:
user.role.value


ব্যবহার করছি।
3. Import check
uv run python -c "from app.services.auth_service import AuthService; print('Login service OK')"

Expected:
Login service OK

এটা pass করলে next step-এ POST /api/v1/auth/login endpoint বানাবো এবং Swagger থেকে actual registered user দিয়ে login করে JWT verify করবো।