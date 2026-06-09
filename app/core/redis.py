import redis.asyncio as aioredis
from app.core.config import settings

# Single shared connection pool for the whole app
redis_client: aioredis.Redis = aioredis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
)

REFRESH_TOKEN_PREFIX = "refresh_token:"
REFRESH_TOKEN_TTL = 60 * 60 * 24 * 30  # 30 days in seconds


async def store_refresh_token(token: str, user_id: str) -> None:
    """Save a refresh token → user_id mapping with 30-day TTL."""
    await redis_client.set(
        f"{REFRESH_TOKEN_PREFIX}{token}",
        user_id,
        ex=REFRESH_TOKEN_TTL,
    )


async def get_refresh_token_owner(token: str) -> str | None:
    """Return the user_id that owns this refresh token, or None if missing/expired."""
    return await redis_client.get(f"{REFRESH_TOKEN_PREFIX}{token}")


async def revoke_refresh_token(token: str) -> None:
    """Delete a refresh token — used on logout, rotation, and ban."""
    await redis_client.delete(f"{REFRESH_TOKEN_PREFIX}{token}")
