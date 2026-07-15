import json
from uuid import UUID
from redis.asyncio import Redis
from app.core.logging import get_logger

logger = get_logger("core.cache")

# ── TTLs ──────────────────────────────────────────────────────────────────────
TTL_INTERESTS       = 86400      # 24h  — seed data, never changes at runtime
TTL_PROMPTS         = 86400      # 24h  — seed data, never changes at runtime
TTL_LOCATIONS       = 604800     # 7d   — countries/provinces/cities
TTL_SYSTEM_STATUS   = 60         # 60s  — /system/status
TTL_SUB_PLANS       = 3600       # 1h   — /subscriptions/plans
TTL_USER_PROFILE    = 600        # 10m  — /users/me
TTL_USER_PHOTOS     = 600        # 10m  — /users/me/photos
TTL_DAILY_LIMITS    = None       # dynamic — until midnight


# ── Cache Keys ────────────────────────────────────────────────────────────────
def key_interests() -> str:
    return "cache:interests:all"

def key_prompts(language: str) -> str:
    return f"cache:prompts:{language}"

def key_countries() -> str:
    return "cache:locations:countries"

def key_provinces(country: str) -> str:
    return f"cache:locations:provinces:{country}"

def key_cities(country: str, province: str) -> str:
    return f"cache:locations:cities:{country}:{province}"

def key_system_status() -> str:
    return "cache:system:status"

def key_sub_plans() -> str:
    return "cache:subscriptions:plans"

def key_user_profile(user_id: UUID) -> str:
    return f"cache:user:{user_id}:profile"

def key_user_photos(user_id: UUID) -> str:
    return f"cache:user:{user_id}:photos"

def key_daily_limits(user_id: UUID, date: str) -> str:
    return f"cache:limits:{user_id}:{date}"


# ── Helpers ───────────────────────────────────────────────────────────────────
async def cache_get(redis: Redis, key: str):
    """Get and deserialize a cached value. Returns None on miss."""
    try:
        raw = await redis.get(key)
        return json.loads(raw) if raw else None
    except Exception:
        return None


async def cache_set(redis: Redis, key: str, value, ttl: int):
    """Serialize and store a value with TTL."""
    try:
        await redis.set(key, json.dumps(value, default=str), ex=ttl)
    except Exception:
        pass


async def invalidate_user_cache(redis: Redis, user_id: UUID):
    """Invalidate all cached data for a user."""
    keys = [
        key_user_profile(user_id),
        key_user_photos(user_id),
    ]
    try:
        await redis.delete(*keys)
    except Exception:
        pass


# ── Discover Card Stack ──────────────────────────────────────────────────────
DISCOVER_STACK_TTL = 1800    # 30 minutes
DISCOVER_STACK_SIZE = 50     # pre-fetch 50 cards at a time
SWIPED_SET_TTL = 7 * 86400   # 7 days


def key_discover_stack(user_id: UUID) -> str:
    return f"cache:discover:{user_id}:stack"


async def pop_discover_stack(redis: Redis, user_id: UUID, count: int) -> list[str]:
    """Pop `count` user IDs from the cached discover stack."""
    key = key_discover_stack(user_id)
    try:
        pipe = redis.pipeline()
        pipe.lrange(key, 0, count - 1)
        pipe.ltrim(key, count, -1)
        results = await pipe.execute()
        return results[0]
    except Exception:
        return []


async def set_discover_stack(redis: Redis, user_id: UUID, user_ids: list[str]):
    """Replace the discover stack with a new list of user IDs."""
    key = key_discover_stack(user_id)
    try:
        await redis.delete(key)
        if user_ids:
            await redis.lpush(key, *reversed(user_ids))
            await redis.expire(key, DISCOVER_STACK_TTL)
    except Exception:
        pass


async def invalidate_discover_stack(redis: Redis, user_id: UUID):
    """Invalidate discover stack (e.g. on location update)."""
    try:
        await redis.delete(key_discover_stack(user_id))
    except Exception:
        pass


# ── Swipe Deduplication ──────────────────────────────────────────────────────

async def record_swipe_cache(redis: Redis, swiper_id: UUID, swipee_id: UUID):
    """Add a swipe to the Redis set for fast exclusion in discover."""
    key = f"swiped:{swiper_id}"
    try:
        await redis.sadd(key, str(swipee_id))
        await redis.expire(key, SWIPED_SET_TTL)
    except Exception:
        pass


async def get_swiped_ids(redis: Redis, user_id: UUID) -> set[str]:
    """Get all swiped user IDs from Redis set."""
    key = f"swiped:{user_id}"
    try:
        members = await redis.smembers(key)
        return {m for m in members}
    except Exception:
        return set()
