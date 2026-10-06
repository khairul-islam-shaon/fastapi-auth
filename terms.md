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
