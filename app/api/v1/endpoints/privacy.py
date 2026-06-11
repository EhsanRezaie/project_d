from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.models.user import User
from app.schemas.privacy import PrivacySettingsResponse, PrivacySettingsUpdate

router = APIRouter(prefix="/privacy", tags=["privacy"])


@router.get("/settings", response_model=PrivacySettingsResponse)
@limiter.limit("60/minute")
async def get_privacy_settings(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """Get current privacy settings"""
    return PrivacySettingsResponse(
        hide_last_seen=current_user.hide_last_seen
    )


@router.patch("/settings", response_model=PrivacySettingsResponse)
@limiter.limit("30/minute")
async def update_privacy_settings(
    request: Request,
    body: PrivacySettingsUpdate,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """Update privacy settings"""
    
    if body.hide_last_seen is not None:
        current_user.hide_last_seen = body.hide_last_seen
    
    await session.commit()
    await session.refresh(current_user)
    
    return PrivacySettingsResponse(
        hide_last_seen=current_user.hide_last_seen
    )