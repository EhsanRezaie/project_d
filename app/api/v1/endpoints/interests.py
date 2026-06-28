from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_session
from app.models.interest import Interest
from app.schemas.interest import InterestResponse

router = APIRouter(prefix="/interests", tags=["interests"])


@router.get("", response_model=list[InterestResponse])
async def get_interests(
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> list[InterestResponse]:
    response.headers["Cache-Control"] = "public, max-age=86400"
    """
    Get the full list of selectable interests.

    Public, no auth required — this is static reference data used to
    populate the interests picker during onboarding and profile editing.
    `name` is a stable key, not display text; resolve to a localized
    label client-side.
    """
    result = await session.execute(
        select(Interest).order_by(Interest.category, Interest.name)
    )
    interests = result.scalars().all()
    return [InterestResponse.model_validate(i) for i in interests]