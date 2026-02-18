"""Authentication Endpoints."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.middleware.auth import (
    create_access_token,
    get_current_active_user,
    verify_password,
)
from app.models import User
from app.schemas import Token, UserLogin, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])

# Account lock settings
MAX_LOGIN_FAILURES = 5
LOCK_DURATION_MINUTES = 30


@router.post("/login", response_model=Token)
async def login(
    request_body: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """Authenticate user and return JWT."""
    result = await db.execute(select(User).where(User.email == request_body.email))
    user = result.scalar_one_or_none()

    if user is None or not verify_password(request_body.password, user.pwd):
        # Increment failure count if user exists
        if user is not None:
            user.failure = (user.failure or 0) + 1
            if user.failure >= MAX_LOGIN_FAILURES:
                user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCK_DURATION_MINUTES)
            await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )

    # Check account lock
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is temporarily locked due to too many failed attempts",
        )

    # Reset failure count on successful login
    user.failure = 0
    user.locked_until = None
    user.last_login = datetime.now(timezone.utc)
    await db.commit()

    expires_delta = timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    access_token = create_access_token(
        data={"sub": user.email},
        expires_delta=expires_delta,
    )

    return Token(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_active_user)):
    """Get current authenticated user."""
    return UserResponse.model_validate(current_user)
