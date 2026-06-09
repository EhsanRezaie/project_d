from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests

from app.db.session import get_session
from app.models.user import User
import app.core.redis as redis
from app.core.config import settings
from app.core.limiter import limiter
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
)

from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    GoogleAuthRequest,
    RefreshRequest,
    CompleteProfileRequest,
    TokenResponse,
    UserResponse,
)

router = APIRouter(prefix="/auth", tags=["auth"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _build_token_response(user: User) -> TokenResponse:
    """Create access + refresh tokens, store refresh in Redis, return response."""
    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    await redis.store_refresh_token(refresh_token, str(user.id))
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


async def _get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def _get_user_by_id(session: AsyncSession, user_id: str) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def _get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> User:
    """Extract and validate Bearer token, return the User object."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token.")
    token = auth_header.split(" ", 1)[1]
    user_id = decode_access_token(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token.")
    user = await _get_user_by_id(session, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or deactivated.")
    return user


# ---------------------------------------------------------------------------
# POST /auth/register
# ---------------------------------------------------------------------------

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def register(
    request: Request,
    body: RegisterRequest,
    session: AsyncSession = Depends(get_session),
):
    existing = await _get_user_by_email(session, body.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )

    user = User(
        email=body.email,
        password_hash=hash_password(body.password),
        name=body.name,
        age=body.age,
        gender=body.gender,
        is_profile_complete=True,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return await _build_token_response(user)


# ---------------------------------------------------------------------------
# POST /auth/login
# ---------------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
async def login(
    request: Request,
    body: LoginRequest,
    session: AsyncSession = Depends(get_session),
):
    user = await _get_user_by_email(session, body.email)

    if not user or not user.password_hash or not verify_password(body.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account has been deactivated.",
        )

    return await _build_token_response(user)


# ---------------------------------------------------------------------------
# POST /auth/google
# ---------------------------------------------------------------------------

@router.post("/google", response_model=TokenResponse)
@limiter.limit("10/minute")
async def google_auth(
    request: Request,
    body: GoogleAuthRequest,
    session: AsyncSession = Depends(get_session),
):
    try:
        id_info = google_id_token.verify_oauth2_token(
            body.id_token,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID,
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token.",
        )

    google_id = id_info["sub"]
    email = id_info.get("email")
    name = id_info.get("name") or email.split("@")[0]

    result = await session.execute(select(User).where(User.google_id == google_id))
    user = result.scalar_one_or_none()

    if not user:
        user = await _get_user_by_email(session, email)
        if user:
            # Existing email user — just link Google
            user.google_id = google_id
        else:
            # Brand new Google user — mark profile incomplete
            user = User(
                email=email,
                google_id=google_id,
                name=name,
                age=18,         # placeholder
                gender="male",  # placeholder
                is_profile_complete=False,
            )
            session.add(user)

    await session.commit()
    await session.refresh(user)

    return await _build_token_response(user)


# ---------------------------------------------------------------------------
# POST /auth/complete-profile
# ---------------------------------------------------------------------------

@router.post("/complete-profile", response_model=TokenResponse)
@limiter.limit("10/minute")
async def complete_profile(
    request: Request,
    body: CompleteProfileRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(_get_current_user),
):
    """
    Called by Google OAuth users after first login.
    Sets real age, gender (and optionally name), marks profile complete.
    Returns a fresh token pair so the updated UserResponse reaches the client.
    """
    if current_user.is_profile_complete:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Profile is already complete.",
        )

    current_user.age = body.age
    current_user.gender = body.gender
    if body.name:
        current_user.name = body.name
    current_user.is_profile_complete = True

    await session.commit()
    await session.refresh(current_user)

    return await _build_token_response(current_user)


# ---------------------------------------------------------------------------
# POST /auth/refresh  —  Rotation: old token revoked, new token issued
# ---------------------------------------------------------------------------

@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
async def refresh(
    request: Request,
    body: RefreshRequest,
    session: AsyncSession = Depends(get_session),
):
    # Step 1: verify JWT signature + expiry
    user_id = decode_refresh_token(body.refresh_token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    # Step 2: check token exists in Redis (not revoked)
    stored_user_id = await redis.get_refresh_token_owner(body.refresh_token)
    if not stored_user_id or stored_user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked.",
        )

    # Step 3: load user
    user = await _get_user_by_id(session, user_id)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or deactivated.",
        )

    # Step 4: revoke old token (rotation)
    await redis.revoke_refresh_token(body.refresh_token)

    # Step 5: issue new token pair
    return await _build_token_response(user)


# ---------------------------------------------------------------------------
# POST /auth/logout
# ---------------------------------------------------------------------------

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def logout(request: Request, body: RefreshRequest):
    """
    Revoke the refresh token immediately.
    Access token stays valid until expiry — client must discard both locally.
    """
    await redis.revoke_refresh_token(body.refresh_token)