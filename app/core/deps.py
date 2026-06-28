from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from jose import JWTError, jwt
from uuid import UUID

from sqlalchemy.orm import selectinload
from app.db.session import get_session
from app.models.user import User
from app.core.config import settings
from app.core.security import decode_token, ACCESS_TOKEN_TYPE
from app.core.logging import get_logger

logger = get_logger("core.deps")

# HTTP Bearer security
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> User:
    """Extract and validate Bearer token, return the User object with profile and settings."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    payload = decode_token(token, ACCESS_TOKEN_TYPE)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    token_version = payload.get("ver", 1)
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )
    
    # Load user with profile and settings using selectinload
    result = await session.execute(
        select(User)
        .options(
            selectinload(User.profile),
            selectinload(User.settings),
        )
        .where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated",
        )
    
    if token_version != user.token_version:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token revoked. Please login again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UUID:
    """
    Lightweight dependency — validates JWT only, zero DB queries.
    Returns user_id as UUID.
    Use for endpoints that only need current_user.id:
      POST /swipes, POST /messages/delivered, POST /messages/read,
      DELETE /messages/{message_id}, POST /notifications/read,
      DELETE /notifications/{id}, POST /blocks/{id}/block,
      POST /blocks/{id}/unblock, POST /reports/{user_id}
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = decode_token(credentials.credentials, ACCESS_TOKEN_TYPE)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return UUID(user_id)


async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Alias for get_current_user - ensures user is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user",
        )
    return current_user


async def get_current_premium_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Requires premium subscription."""
    if not current_user.profile or not current_user.profile.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required",
        )
    return current_user


async def get_current_user_ws(token: str) -> str | None:
    """Get current user ID from WebSocket token"""
    from app.core.security import decode_access_token
    return decode_access_token(token)


async def get_admin_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User:
    """Verify admin access using X-Admin-Key header only (no JWT required)"""
    admin_key = request.headers.get("X-Admin-Key")
    
    if not admin_key or admin_key != settings.ADMIN_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Get existing admin user from database
    result = await session.execute(
        select(User).options(selectinload(User.profile)).where(User.email == "admin@test.com")
    )
    admin_user = result.scalar_one_or_none()
    
    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin user not found in database. Please run setup."
        )
    
    return admin_user