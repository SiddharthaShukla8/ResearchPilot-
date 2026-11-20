"""FastAPI authentication dependencies and user context extraction.

Security policy:
- Authentication is EXCLUSIVELY via the HTTP Authorization header
  using the Bearer scheme (RFC 6750 Section 2.1).
- Query-string tokens, cookie-based tokens, and form-encoded tokens
  are intentionally NOT accepted to prevent token leakage through
  browser history, server access logs, referrer headers, and proxy caches.
- All endpoints that require authentication depend on `get_current_user`.
"""
import logging

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import PyJWTError
from sqlalchemy.ext.asyncio import AsyncSession

from researchpilot.core.security import decode_token
from researchpilot.db.models import User
from researchpilot.db.session import get_db_session
from researchpilot.repositories.auth_repo import AuthRepository

logger = logging.getLogger(__name__)

# Strictly enforce Authorization header; no auto_error so we control the message.
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    session: AsyncSession = Depends(get_db_session),
) -> User:
    """Validate Bearer JWT access token and return the authenticated User.

    Raises HTTP 401 with WWW-Authenticate: Bearer on any failure:
    missing credentials, invalid/expired token, inactive user.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials were not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type",
                headers={"WWW-Authenticate": "Bearer"},
            )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload missing subject identifier",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except PyJWTError:
        logger.warning("JWT validation failed for incoming request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials or token expired",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth_repo = AuthRepository(session)
    user = await auth_repo.get_user_by_id(user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account inactive or not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
