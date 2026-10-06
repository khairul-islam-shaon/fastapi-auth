সংক্ষেপে প্রতিটা folder/file-এর কাজ:
- app/main.py → FastAPI app start point
- app/api/router.py → সব API router একসাথে register করবে
- app/api/v1/auth.py → login, register, refresh, logout
- app/api/v1/users.py → user profile/user-related endpoints
- app/api/v1/admin.py → admin-only endpoints
- app/core/config.py → .env, app settings, secret config load করবে
- app/core/security.py → password hashing, JWT create/decode
- app/core/exceptions.py → common/custom error handling
- app/db/session.py → PostgreSQL connection + DB session
- app/db/base.py → SQLAlchemy Base
- app/db/models/user.py → users table structure
- app/schemas/auth.py → login/register/token request-response validation
- app/schemas/user.py → user request-response validation
- app/services/auth_service.py → authentication business logic
- app/services/user_service.py → user-related business logic
- app/dependencies/auth.py → get_current_user(), token check
- app/dependencies/permissions.py → ADMIN/MANAGER/USER role check
- tests/ → automated testing
Flowটা হবে: