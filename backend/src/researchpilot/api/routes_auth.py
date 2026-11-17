"""Authentication API routes."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from researchpilot.api.deps import get_current_user
from researchpilot.api.schemas.auth_schemas import (
    TokenRefreshRequest,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)
from researchpilot.core.security import (
    create_access_token,
    create_refresh_token,
    verify_password,
)
from researchpilot.db.models import User
from researchpilot.db.session import get_db_session
from researchpilot.repositories.auth_repo import AuthRepository

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserRegisterRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Register a new user account and issue auth tokens."""
    repo = AuthRepository(session)
    existing = await repo.get_user_by_email(payload.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email address already exists",
        )

    user = await repo.create_user(payload.name, payload.email, payload.password)
    access_token = create_access_token({"sub": user.id, "email": user.email})
    raw_refresh, expire_dt = create_refresh_token({"sub": user.id})
    await repo.create_refresh_session(user.id, raw_refresh, expire_dt)

    return TokenResponse(access_token=access_token, refresh_token=raw_refresh)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: UserLoginRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Authenticate user credentials and issue auth tokens."""
    repo = AuthRepository(session)
    user = await repo.get_user_by_email(payload.email)
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    access_token = create_access_token({"sub": user.id, "email": user.email})
    raw_refresh, expire_dt = create_refresh_token({"sub": user.id})
    await repo.create_refresh_session(user.id, raw_refresh, expire_dt)

    return TokenResponse(access_token=access_token, refresh_token=raw_refresh)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    payload: TokenRefreshRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Rotate and refresh an active session."""
    repo = AuthRepository(session)
    refresh_session = await repo.get_active_refresh_session(payload.refresh_token)
    if not refresh_session:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid, expired, or revoked refresh token",
        )

    # Revoke old session token (rotation)
    await repo.revoke_refresh_session(payload.refresh_token)

    user = await repo.get_user_by_id(refresh_session.user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is not active",
        )

    access_token = create_access_token({"sub": user.id, "email": user.email})
    raw_refresh, expire_dt = create_refresh_token({"sub": user.id})
    await repo.create_refresh_session(user.id, raw_refresh, expire_dt)

    return TokenResponse(access_token=access_token, refresh_token=raw_refresh)


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    payload: TokenRefreshRequest,
    session: AsyncSession = Depends(get_db_session),
):
    """Revoke user refresh session."""
    repo = AuthRepository(session)
    await repo.revoke_refresh_session(payload.refresh_token)
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Return profile details of the authenticated user."""
    return current_user
