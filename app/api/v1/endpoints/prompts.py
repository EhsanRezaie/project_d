from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_session
from app.models.prompt import Prompt
from app.schemas.prompt import PromptResponse

router = APIRouter(prefix="/prompts", tags=["prompts"])


@router.get("", response_model=list[PromptResponse])
async def get_prompts(
    language: str = Query("fa", min_length=2, max_length=5, description="Language code, e.g. 'fa' or 'en'"),
    session: AsyncSession = Depends(get_session),
) -> list[PromptResponse]:
    """
    Get the list of active prompt questions in the requested language.

    Public, no auth required. Defaults to 'fa'. Only `is_active=True`
    prompts are returned — inactive prompts are kept in the DB (e.g. for
    existing UserPrompt answers referencing them) but no longer offered
    as a choice for new answers.
    """
    result = await session.execute(
        select(Prompt)
        .where(Prompt.language == language, Prompt.is_active == True)  # noqa: E712
        .order_by(Prompt.category, Prompt.id)
    )
    prompts = result.scalars().all()
    return [PromptResponse.model_validate(p) for p in prompts]