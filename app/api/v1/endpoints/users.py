from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func  # ADD THIS IMPORT
from datetime import datetime, timezone  # ADD THIS

from app.db.session import get_session
from app.models.user import User
from app.core.deps import get_current_user
from app.core.limiter import limiter

from app.schemas.user import UserResponse, UserUpdateRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserResponse)
@limiter.limit("100/minute")
async def get_me(
    request: Request,
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get current user's profile.
    Requires valid access token.
    """
    return UserResponse.model_validate(current_user)


@router.put("/me", response_model=UserResponse)
@limiter.limit("30/minute")
async def update_me(
    request: Request,
    update_data: UserUpdateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Update current user's profile.
    All fields are optional - only provided fields will be updated.
    """
    update_dict = update_data.model_dump(exclude_unset=True)
    
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update",
        )
    
    for field, value in update_dict.items():
        setattr(current_user, field, value)
    
    if not current_user.is_profile_complete and ("age" in update_dict or "gender" in update_dict):
        if current_user.age and current_user.gender:
            current_user.is_profile_complete = True
    
    await session.commit()
    await session.refresh(current_user)
    
    return UserResponse.model_validate(current_user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("5/minute")
async def delete_me(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Soft delete current user account.
    Sets is_active to False instead of hard delete.
    """
    current_user.is_active = False
    await session.commit()


@router.post("/me/location", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("60/minute")
async def update_location(
    request: Request,
    lat: float,
    lng: float,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Update user's current location (lat/lng).
    Called when app opens or user moves.
    """
    if lat < -90 or lat > 90:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Latitude must be between -90 and 90",
        )
    
    if lng < -180 or lng > 180:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Longitude must be between -180 and 180",
        )
    
    current_user.lat = lat
    current_user.lng = lng
    current_user.last_seen_at = datetime.now(timezone.utc)  # FIXED: use datetime instead of func.now()
    
    await session.commit()