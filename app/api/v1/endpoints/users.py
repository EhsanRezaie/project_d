# app/api/v1/endpoints/users.py
import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select ,delete 
from app.models.user_interest import UserInterest 
from app.models.user_prompt import UserPrompt
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone  
from app.models.interest import Interest
from app.db.session import get_session
from app.models.user import User
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.services.location_service import LocationService
from app.schemas.user import UserProfileResponse, UserUpdateRequest, LocationTextUpdateRequest, LocationTextUpdateResponse,InterestUpdateRequest,PromptUpdateRequest

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserProfileResponse)
@limiter.limit("100/minute")
async def get_me(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:

    # Always reload with relationships loaded
    result = await session.execute(
        select(User)
        .options(
            selectinload(User.profile),
            selectinload(User.settings),
            selectinload(User.user_interests).selectinload(UserInterest.interest),
            selectinload(User.prompts).selectinload(UserPrompt.prompt),
        )
        .where(User.id == current_user.id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserProfileResponse.model_validate(user)


@router.put("/me", response_model=UserProfileResponse)
@limiter.limit("30/minute")
async def update_me(
    request: Request,
    update_data: UserUpdateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
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
    
    # Update profile fields (they are in UserProfile, not User)
    profile = current_user.profile
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )
    
    # Fields that belong to UserProfile
    profile_fields = ['name', 'bio', 'birth_date', 'gender', 'height', 'weight', 
                  'body_type', 'relationship_status', 'living_situation',
                  'children_status', 'smoking', 'drinking', 'education',
                  'workplace', 'religion', 'ethnicity', 'political_orientation',
                  'sexual_orientation', 'languages']
    
    for field, value in update_dict.items():
        if field in profile_fields:
            setattr(profile, field, value)
        else:
            # Fields that belong to User (like age is computed from birth_date)
            setattr(current_user, field, value)
    
    # Update last_seen
    current_user.last_seen_at = datetime.now(timezone.utc)
    
    await session.commit()
    await session.refresh(current_user)
    
    # Reload with profile, settings, user_interests, and prompts
    result = await session.execute(
        select(User)
        .options(
            selectinload(User.profile),
            selectinload(User.settings),
            selectinload(User.user_interests).selectinload(UserInterest.interest),
            selectinload(User.prompts).selectinload(UserPrompt.prompt),
        )
        .where(User.id == current_user.id)
    )
    user = result.scalar_one_or_none()
    
    return UserProfileResponse.model_validate(user)


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
    If user hasn't manually set location text, auto-fill country/province/city from coordinates.
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
    
    # Update location in UserProfile
    profile = current_user.profile
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )
    
    profile.lat = lat
    profile.lng = lng
    current_user.last_seen_at = datetime.now(timezone.utc)
    
    # Auto-fill location text from coordinates (only if user didn't manually set)
    if not profile.location_manual:
        location_data = await LocationService.reverse_geocode(lat, lng)
        if location_data:
            if location_data.get("country"):
                profile.country = location_data.get("country")
            if location_data.get("province"):
                profile.province = location_data.get("province")
            if location_data.get("city"):
                profile.city = location_data.get("city")
    
    await session.commit()


@router.patch("/me/location-text", response_model=LocationTextUpdateResponse)
@limiter.limit("30/minute")
async def update_location_text(
    request: Request,
    body: LocationTextUpdateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Update user's location with text fields (country, province, city).
    """
    profile = current_user.profile
    if not profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User profile not found",
        )
    
    # Update fields - no validation needed
    if body.country is not None:
        profile.country = body.country
    if body.province is not None:
        profile.province = body.province
    if body.city is not None:
        profile.city = body.city
    
    # Set location_manual to True if any text field was updated
    if body.province is not None or body.city is not None or body.country is not None:
        if body.province or body.city or body.country:
            profile.location_manual = True
    
    await session.commit()
    await session.refresh(current_user)
    
    return LocationTextUpdateResponse(
        country=profile.country,
        province=profile.province,
        city=profile.city,
        location_manual=profile.location_manual
    )


@router.put("/me/interests", response_model=UserProfileResponse)
@limiter.limit("30/minute")
async def update_interests(
    request: Request,
    update_data: InterestUpdateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    """
    Update current user's interests.
    Replaces all existing interests with the new list.
    """
    # Get all interest names from database
    result = await session.execute(
        select(Interest).where(Interest.name.in_(update_data.interests))
    )
    existing_interests = result.scalars().all()
    
    # Check if all provided interests exist
    existing_names = {i.name for i in existing_interests}
    provided_names = set(update_data.interests)
    missing_names = provided_names - existing_names
    
    if missing_names:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid interests: {', '.join(missing_names)}"
        )
    
    # Delete all existing user interests
    await session.execute(
        delete(UserInterest).where(UserInterest.user_id == current_user.id)
    )
    
    # Create new user interests
    for interest in existing_interests:
        user_interest = UserInterest(
            user_id=current_user.id,
            interest_id=interest.id,
        )
        session.add(user_interest)
    
    await session.commit()
    await session.refresh(current_user)
    
    # Reload with profile, settings, user_interests, and prompts
    result = await session.execute(
        select(User)
        .options(
            selectinload(User.profile),
            selectinload(User.settings),
            selectinload(User.user_interests).selectinload(UserInterest.interest),
            selectinload(User.prompts).selectinload(UserPrompt.prompt),
        )
        .where(User.id == current_user.id)
    )
    user = result.scalar_one_or_none()
    
    return UserProfileResponse.model_validate(user)


@router.put("/me/prompts", response_model=UserProfileResponse)
@limiter.limit("30/minute")
async def update_prompts(
    request: Request,
    update_data: PromptUpdateRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserProfileResponse:
    """
    Update current user's prompts.
    Replaces all existing prompts with the new list.
    """
    # Delete all existing user prompts
    await session.execute(
        delete(UserPrompt).where(UserPrompt.user_id == current_user.id)
    )
    
    # Create new user prompts
    for prompt_data in update_data.prompts:
        user_prompt = UserPrompt(
            user_id=current_user.id,
            prompt_id=uuid.UUID(prompt_data["prompt_id"]),
            answer=prompt_data["answer"],
        )
        session.add(user_prompt)
    
    await session.commit()
    await session.refresh(current_user)
    
    # Reload with profile, settings, user_interests, and prompts
    result = await session.execute(
        select(User)
        .options(
            selectinload(User.profile),
            selectinload(User.settings),
            selectinload(User.user_interests).selectinload(UserInterest.interest),
            selectinload(User.prompts).selectinload(UserPrompt.prompt),
        )
        .where(User.id == current_user.id)
    )
    user = result.scalar_one_or_none()
    
    return UserProfileResponse.model_validate(user)