from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# ---------------------------------------------------------------------------
# Password hashing
# ---------------------------------------------------------------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(plain: str) -> str:
    """Hash a plain-text password."""
    return pwd_context.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain matches the stored hash."""
    return pwd_context.verify(plain, hashed)


# ---------------------------------------------------------------------------
# JWT
# ---------------------------------------------------------------------------

# Token types — stored in the payload so we can distinguish them
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"

REFRESH_TOKEN_EXPIRE_DAYS = 30


def _create_token(subject: str, token_type: str, expires_delta: timedelta) -> str:
    """
    Internal helper — build and sign a JWT.
    `subject` is always the user UUID as a string.
    """
    expire = datetime.now(timezone.utc) + expires_delta
    payload = {
        "sub": subject,
        "type": token_type,
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_access_token(user_id: str) -> str:
    """Return a signed access token valid for ACCESS_TOKEN_EXPIRE_MINUTES."""
    return _create_token(
        subject=user_id,
        token_type=ACCESS_TOKEN_TYPE,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: str) -> str:
    """Return a signed refresh token valid for REFRESH_TOKEN_EXPIRE_DAYS."""
    return _create_token(
        subject=user_id,
        token_type=REFRESH_TOKEN_TYPE,
        expires_delta=timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str, expected_type: str) -> Optional[str]:
    """
    Decode and validate a JWT.
    Returns the user UUID string on success, None on any failure.
    Checks:
      - signature valid
      - not expired
      - token type matches expected_type
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != expected_type:
            return None
        return payload.get("sub")
    except JWTError:
        return None


def decode_access_token(token: str) -> Optional[str]:
    return decode_token(token, ACCESS_TOKEN_TYPE)


def decode_refresh_token(token: str) -> Optional[str]:
    return decode_token(token, REFRESH_TOKEN_TYPE)