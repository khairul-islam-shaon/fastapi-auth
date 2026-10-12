from fastapi import APIRouter, Depends

from app.db.models.user import User, UserRole
from app.dependencies.permissions import require_roles


router = APIRouter(
    prefix="/admin",
    tags=["Admin"],
)


@router.get("/dashboard")
async def admin_dashboard(
    current_user: User = Depends(
        require_roles(UserRole.ADMIN)
    ),
):
    return {
        "message": "Welcome Admin",
        "user_id": str(current_user.id),
        "role": current_user.role,
    }