from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_session
from app.models.interest import Interest
from app.schemas.interest import InterestResponse
from app.core.redis import redis_client
from app.core.cache import cache_get, cache_set, key_interests, TTL_INTERESTS

from app.core.logging import get_logger

logger = get_logger("interests")

router = APIRouter(prefix="/interests", tags=["interests"])


@router.get("", response_model=list[InterestResponse])
async def get_interests(
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> list[InterestResponse]:
    """
    Get the full list of selectable interests.

    Public, no auth required — this is static reference data used to
    populate the interests picker during onboarding and profile editing.
    `name` is a stable key, not display text; resolve to a localized
    label client-side.
    """
    response.headers["Cache-Control"] = "public, max-age=86400"
    cached = await cache_get(redis_client, key_interests())
    if cached:
        return [InterestResponse(**i) for i in cached]
    result = await session.execute(
        select(Interest).order_by(Interest.category, Interest.name)
    )
    interests = result.scalars().all()
    data = [InterestResponse.model_validate(i).model_dump(mode='json') for i in interests]
    await cache_set(redis_client, key_interests(), data, TTL_INTERESTS)
    return [InterestResponse(**i) for i in data]