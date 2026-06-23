# app/api/v1/endpoints/discover.py
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from uuid import UUID
from math import radians, sin, cos, sqrt, atan2
from datetime import date, timedelta

from app.db.session import get_session
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.user_settings import UserSettings
from app.models.photo import Photo
from app.models.swipe import Swipe
from app.models.match import Match
from app.models.block import Block
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.schemas.discover import ProfileResponse, DiscoverResponse

router = APIRouter(prefix="/discover", tags=["discover"])


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in km between two coordinates using Haversine formula"""
    if not lat1 or not lng1 or not lat2 or not lng2:
        return None
    
    R = 6371  # Earth's radius in km
    
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lng = radians(lng2 - lng1)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c


@router.get("", response_model=DiscoverResponse)
@limiter.limit("60/minute")
async def discover(
    request: Request,
    age_min: int = Query(18, ge=18, le=100),
    age_max: int = Query(100, ge=18, le=100),
    gender: str = Query(None, pattern="^(male|female)$"),
    distance_km: int = Query(50, ge=1, le=500),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DiscoverResponse:
    """
    Discover page for swiping.
    Users you've swiped on (like OR pass) are excluded.
    Users you blocked are excluded.
    Users who blocked you are excluded.
    Users you already matched with are excluded.
    Filters by gender if provided, otherwise shows all genders.
    """
    
    # Get current user with profile
    user_result = await session.execute(
        select(User)
        .options(
            selectinload(User.profile),
            selectinload(User.settings),
            selectinload(User.photos),
        )
        .where(User.id == current_user.id)
    )
    current_user_full = user_result.scalar_one_or_none()
    
    if not current_user_full or not current_user_full.profile:
        return DiscoverResponse(users=[], total=0, next_offset=None)
    
    current_profile = current_user_full.profile
    
    # Calculate birth date range from age
    today = date.today()
    
    # For age_min: max_birth_date = today - age_min years (youngest)
    # For age_max: min_birth_date = today - (age_max + 1) years (oldest)
    max_birth_date = today - timedelta(days=age_min * 365)
    min_birth_date = today - timedelta(days=(age_max + 1) * 365)
    
    # Subquery: users current user has already swiped on
    swiped_user_ids = select(Swipe.to_user).where(
        Swipe.from_user == current_user.id
    ).subquery()
    
    # Subquery: users current user has blocked
    blocked_user_ids = select(Block.blocked_id).where(
        Block.blocker_id == current_user.id
    ).subquery()
    
    # Subquery: users who have blocked current user
    blocked_by_user_ids = select(Block.blocker_id).where(
        Block.blocked_id == current_user.id
    ).subquery()
    
    # Subquery: users current user has matched with
    matched_as_user1 = select(Match.user2_id).where(
        Match.user1_id == current_user.id,
        Match.is_active == True
    )
    matched_as_user2 = select(Match.user1_id).where(
        Match.user2_id == current_user.id,
        Match.is_active == True
    )
    matched_user_ids = matched_as_user1.union(matched_as_user2).subquery()
    
    # Base query with eager loading
    query = select(User).options(
        selectinload(User.profile),
        selectinload(User.settings),
        selectinload(User.photos),
    ).join(UserProfile, User.id == UserProfile.user_id).where(
        User.is_active == True,
        User.id != current_user.id,
        UserProfile.birth_date.between(min_birth_date, max_birth_date),
        User.id.not_in(select(swiped_user_ids.c.to_user)),
        User.id.not_in(select(blocked_user_ids.c.blocked_id)),
        User.id.not_in(select(blocked_by_user_ids.c.blocker_id)),
        User.id.not_in(select(matched_user_ids.c.user2_id)),
    )
    
    # Gender filter (optional - if not provided, show all genders)
    if gender:
        query = query.where(UserProfile.gender == gender)
    
    # Count total BEFORE pagination
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query)
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    users = result.scalars().all()
    
    # Build response with distances
    response_users = []
    for user in users:
        if not user.profile:
            continue
            
        # Calculate distance
        distance = None
        if current_profile.lat and current_profile.lng and user.profile.lat and user.profile.lng:
            distance = calculate_distance(
                current_profile.lat, current_profile.lng,
                user.profile.lat, user.profile.lng
            )
            if distance and distance > distance_km:
                continue
        
        # Get main photo URL
        main_photo_url = None
        if user.photos:
            main_photo = next((p for p in user.photos if p.is_main and p.status == "approved"), None)
            if main_photo:
                main_photo_url = main_photo.url
        
        response_users.append(ProfileResponse(
            id=user.id,
            name=user.profile.name,
            age=user.profile.age,  # ✅ Uses profile.age property
            gender=user.profile.gender,
            bio=user.profile.bio,
            height=user.profile.height,
            weight=user.profile.weight,
            distance_km=round(distance, 1) if distance else None,
            main_photo_url=main_photo_url,
            is_premium=user.profile.is_premium,
            is_verified=user.phone_verified if user.phone_verified is not None else False,
        ))
    
    # Pagination
    has_more = offset + limit < total
    next_offset = offset + limit if has_more else None
    
    return DiscoverResponse(
        users=response_users,
        next_offset=next_offset,
        total=total,
    )