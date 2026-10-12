from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies.auth import get_current_user
from app.db.models.user import User
from app.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
)
from app.db.session import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService


router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {
            "description": "Email already registered",
        }
    },
)
async def register(
    data: UserCreate,
    session: AsyncSession = Depends(get_db),
) -> UserResponse:
    service = AuthService(session)

    try:
        user = await service.register(data)
    except EmailAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
    responses={
        401: {
            "description": "Invalid email or password",
        }
    },
)
async def login(
    data: LoginRequest,
    session: AsyncSession = Depends(get_db),
) -> TokenResponse:
    service = AuthService(session)

    try:
        access_token = await service.login(data)
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    return TokenResponse(
        access_token=access_token,
    )




@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        401: {
            "description": "Invalid or expired token",
        }
    },
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return current_user