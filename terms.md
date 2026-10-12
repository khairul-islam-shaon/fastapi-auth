\***\*venv** মানে virtual environment।
সহজভাবে বললে, এটা তোমার project-এর জন্য আলাদা Python environment বানায়, যাতে এই project-এর package অন্য project-এর package-এর সাথে conflict না করে।
উদাহরণ:
Project A
FastAPI 0.x
SQLAlchemy 2.x

Project B
Django
Different package versions

venv না থাকলে সব package global Python-এ install হবে। এতে version conflict হতে পারে।
তোমার project-এ:
uv venv

চালালে .venv নামে folder তৈরি হবে।
তার ভিতরে থাকবে:
fastapi-auth/
├── .venv/
├── pyproject.toml
└── ...

তারপর activate করলে:
source .venv/Scripts/activate

তুমি যে package install করবে, সেগুলো এই project-এর .venv-এ থাকবে।
আর uv use করলে অনেক ক্ষেত্রে manually activate করাও বাধ্যতামূলক না; uv run ... দিয়েও project environment ব্যবহার করা যায়। তবে শেখার জন্য .venv conceptটা বুঝে রাখা ভালো।

\***\*Base** কী?
SQLAlchemy-এর সব database model-এর common parent class। User, RefreshToken—সব model এই Base inherit করবে। পরে Alembic এই Base-এর metadata দেখে database table generate/migrate করবে।
Flow:
Base
├── User
└── RefreshToken

User Model কী?
এটা Python class, কিন্তু SQLAlchemy এটাকে PostgreSQL-এর users table-এর সাথে map করবে।
Python User class
↕
PostgreSQL users table

Mapped / mapped_column কেন?
এগুলো SQLAlchemy 2.x-এর modern typed ORM syntax। এতে Python type + database column definition clean থাকে।

**\***Alembic\*\* কী?
Alembic হলো SQLAlchemy-এর migration tool।
ধরো আজ users table-এ আছে:
id
email
password_hash
role

পরে তুমি add করলে:
phone_number

Production database-এ table delete করে আবার create করা যাবে না। Alembic migration safely schema change করে:
Old DB Schema
↓
Migration
↓
New DB Schema

কেন Base.metadata.create_all() ব্যবহার করছি না?
create_all() learning/demo-র জন্য useful, কিন্তু production-grade project-এ এটা migration history রাখে না।
Alembic রাখে:
001_create_users
002_add_phone
003_add_refresh_tokens

তাই database schema version-controlled থাকে।

আগে ৩টা concept
target_metadata কী? Alembic database schema guess করে না। আমাদের Base.metadata দেখে বুঝবে কোন table/column model-এ আছে।
User Model
↓
Base.metadata
↓
Alembic
↓
Migration

Model import কেন দরকার? শুধু Base import করলে Base.metadata জানবে না যে User model আছে। তাই migration generate করার আগে User model import করতে হবে।
Async setup কেন? আমাদের connection হলো:
SQLAlchemy AsyncEngine
↓
asyncpg
↓
PostgreSQL

তাই Alembic migration environment-ও async-compatible করবো।

৩টা concept:

- **\*AsyncSession** → current request-এর database session।
- **\*select()** → SQLAlchemy দিয়ে SELECT ... query বানায়।
- **\*Repository** → শুধু database read/write করবে; password hashing, JWT, role decision এখানে থাকবে না।
  আর একটা important design decision: Repository commit() করবে না। Transaction কখন commit হবে সেটা Service layer control করবে। এতে পরে registration-এর মতো একাধিক DB operation এক transaction-এ রাখা সহজ হবে।
  Flow:
  AuthService
  ↓
  UserRepository
  ↓
  AsyncSession
  ↓
  PostgreSQL

**_flush() আর refresh()_** কেন?
flush():
Python User object
↓
SQL INSERT sent to PostgreSQL
↓
Transaction এখনো commit হয়নি

অর্থাৎ database operation execute হয়, কিন্তু final save Service-এর commit() পর্যন্ত অপেক্ষা করে।
refresh(user) database থেকে generated values আবার object-এ নিয়ে আসে, যেমন:
id
created_at
updated_at

**_Schema কী?_**
এটা database model না। এটা API-র request/response validate করে।
Flow:
Client JSON
↓
Pydantic Schema
↓
Service
↓
Repository
↓
Database

কেন দরকার:

- invalid email reject করবে
- password required কিনা check করবে
- client যেন is_active, role, password_hash নিজের মতো পাঠাতে না পারে
- response-এ password_hash accidentally leak হবে না

AuthService-এর কাজ হবে authentication-এর business logic handle করা।
Register flow:
UserCreate
↓
AuthService.register()
↓
Email already exists?
├── Yes → Error
↓ No
Hash password
↓
Create User object
↓
UserRepository.create()
↓
COMMIT
↓
Return User

এখানে Router database query বা password hash করবে না।

1. Custom exception কেন?
   Duplicate email হলে Service layer থেকে সরাসরি HTTPException raise করবো না। কারণ Service HTTP-এর উপর depend করা উচিত না।
   তাই app/core/exceptions.py:
   class EmailAlreadyExistsError(Exception): pass

পরে Router এই exception-কে 409 Conflict বানাবে। 2. commit() / rollback() কী?
Database transaction:
Changes
↓
commit()
↓
Permanent save

কোনো error হলে:
Error
↓
rollback()
↓
Pending changes cancel

Production code-এ rollback গুরুত্বপূর্ণ, কারণ failed transaction-এর session otherwise unusable হতে পারে।

**_APIRouter_** → related API endpoint group করে
Depends(get_db) → current request-এর জন্য DB session দেয়
response_model=UserResponse → response থেকে শুধু safe field return করে, password_hash leak হতে দেয় না
HTTPException → service-এর business error-কে HTTP response-এ convert করে
409 Conflict → একই email already থাকলে appropriate status
POST /api/v1/auth/register
↓
UserCreate validation
↓
get_db()
↓
AuthService.register()
↓
UserRepository
↓
PostgreSQL
↓
UserResponse


**JWT** কী?
JWT = JSON Web Token।
Login successful হলে server একটা signed token দেবে:
email + password
      ↓
verify user
      ↓
JWT access token
      ↓
client stores token
      ↓
Authorization: Bearer <token>

এর মাধ্যমে প্রতিবার password পাঠাতে হয় না।
PyJWT কেন?
PyJWT Python library যা JWT:
- create/sign করে
- decode করে
- signature verify করে
- expiration validate করে
এখন install করো:
uv add pyjwt

তারপর verify:
uv run python -c "import jwt; print(jwt.__version__)"

JWT secret কেন দরকার?
Token এমন হবে:
payload
   +
JWT_SECRET
   ↓
signed token

Secret ছাড়া কেউ valid token generate করতে পারবে না।
Secret code-এর মধ্যে hardcode করবো না। .env-এ থাকবে।
Strong secret generate করো:
uv run python -c "import secrets; print(secrets.token_urlsafe(64))"

যে value আসবে সেটা copy করে .env-এ রাখো:
JWT_SECRET=<generated-secret>
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

এখানে:
JWT_SECRET
→ token sign করার private secret

HS256
→ signing algorithm

ACCESS_TOKEN_EXPIRE_MINUTES=30
→ token 30 মিনিট valid

এখন app/core/config.py-এর Settings class-এ add করো:
jwt_secret: strjwt_algorithm: str = "HS256"access_token_expire_minutes: int = 30


তাহলে relevant অংশ হবে:
class Settings(BaseSettings):    app_name: str = "FastAPI Auth Service"    app_env: str = "development"    debug: bool = False    database_url: str    jwt_secret: str    jwt_algorithm: str = "HS256"    access_token_expire_minutes: int = 30


তারপর verify:
uv run python -c "from app.core.config import settings; print(settings.jwt_algorithm, settings.access_token_expire_minutes)"

Expected:
HS256 30



***create_access_token()*** login successful হলে token বানাবে।
Token payload roughly:
{
  "sub": "user-uuid",
  "role": "USER",
  "type": "access",
  "exp": 1234567890
}

এখানে:
- sub → কোন user-এর token
- role → RBAC-এর জন্য role
- type → এটা access token নাকি অন্য token
- exp → token কখন expire হবে
decode_access_token() token valid কিনা check করবে এবং payload ফেরত দেবে।




***Protected Route***
নতুন concept: get_current_user()।
এর কাজ হবে request-এর header থেকে token নেওয়া:
Authorization: Bearer <token>

তারপর:
Bearer Token
   ↓
Decode JWT
   ↓
Get user_id from sub
   ↓
Find user in DB
   ↓
Return authenticated User

তারপর /auth/me endpoint বানাবো:
GET /api/v1/auth/me

যেটা valid token দিলে current logged-in user return করবে।



***get_current_user()*** কী?
এটা FastAPI dependency। Protected endpoint-এ request এলে এটি:
Authorization: Bearer <JWT>
          ↓
Token extract
          ↓
JWT verify/decode
          ↓
sub থেকে user UUID
          ↓
UserRepository.get_by_id()
          ↓
Current User

এটা দরকার কারণ প্রত্যেক protected API-তে manually JWT decode করা উচিত না। একবার reusable dependency বানালে পরে:
/auth/me
/admin/...
/users/...

সব জায়গায় একই authentication logic ব্যবহার করতে পারবো।
HTTPBearer কী এবং কেন?
FastAPI-এর HTTPBearer request-এর:
Authorization: Bearer <token>

header parse করে token বের করে দেয়।
আমাদের login JSON body নেয়, তাই এই stage-এ HTTPBearer clean/simple choice। এটা Swagger-এ Authorize option-ও তৈরি করবে।




***/auth/me*** কী?
এটা logged-in user-এর নিজের information return করবে। এটিই প্রথম protected endpoint হবে।
Flow:
GET /api/v1/auth/me
        ↓
Authorization: Bearer <token>
        ↓
get_current_user()
        ↓
JWT validate
        ↓
DB থেকে user load
        ↓
UserResponse

এখন app/api/v1/auth.py-এ এই endpoint add করো:
from app.dependencies.auth import get_current_userfrom app.db.models.user import User


তারপর নিচে add করো:
@router.get(    "/me",    response_model=UserResponse,    responses={        401: {            "description": "Invalid or expired token",        }    },)async def get_me(    current_user: User = Depends(get_current_user),) -> UserResponse:    return current_user


এখন server run থাকলে Swagger refresh করো:
http://127.0.0.1:8000/docs

এখন GET /api/v1/auth/me দেখাবে।
প্রথমে token ছাড়া execute করো।
Expected:
401 Unauthorized

তারপর Swagger-এর Authorize button-এ login API থেকে পাওয়া token দাও।
শুধু token value paste করবে:
eyJ...

তারপর আবার /auth/me execute করো।
Expected response roughly:

  "id": "...",
  "email": "user@example.com",
  "full_name": "Test User",
  "role": "USER",
  "is_active": true,
  "is_verified": false,
  "created_at": "...",
  "updated_at": "..."




  ****RBAC**** কী?
RBAC = Role-Based Access Control
মানে user authenticated হলেই সব route access করতে পারবে না। Role অনুযায়ী permission decide হবে।
আমাদের তিনটা role:
ADMIN
MANAGER
USER

Flow:
JWT
 ↓
get_current_user()
 ↓
Current User
 ↓
require_roles(...)
 ↓
Allowed / 403 Forbidden

require_roles() কী?
এটা reusable FastAPI dependency হবে।
উদাহরণ:
Depends(require_roles(UserRole.ADMIN))


মানে শুধু ADMIN ঢুকতে পারবে।
আর:
Depends(    require_roles(        UserRole.ADMIN,        UserRole.MANAGER,    ))


মানে ADMIN এবং MANAGER দুজনই ঢুকতে পারবে।





Step 1 — ***UserService*** কী?
UserService user-related business logic রাখবে। Router সরাসরি repository call করবে না।
app/services/user_service.py:
from sqlalchemy.ext.asyncio import AsyncSessionfrom app.db.models.user import Userfrom app.repositories.user_repository import UserRepositoryclass UserService:    def __init__(self, session: AsyncSession):        self.user_repository = UserRepository(session)    async def list_users(self) -> list[User]:        return await self.user_repository.list_users()


তারপর verify:
uv run python -c "from app.services.user_service import UserService; print('UserService OK')"

Expected:
UserService OK