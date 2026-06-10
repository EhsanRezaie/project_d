from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.sql import functions
from uuid import UUID
from math import radians, sin, cos, sqrt, atan2

from app.db.session import get_session
from app.models.user import User
from app.models.photo import Photo
from app.models.swipe import Swipe
from app.models.match import Match
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
    distance_km: int = Query(50, ge=1, le=500),
    limit: int = Query(20, ge=1, le=50),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> DiscoverResponse:
    """
    Discover page for swiping.
    Users you've swiped on (like OR pass) are excluded.
    Only shows opposite gender.
    """
    
    # Determine opposite gender
    opposite_gender = "female" if current_user.gender == "male" else "male"
    
    # Subquery: users current user has already swiped on
    swiped_user_ids = select(Swipe.to_user).where(
        Swipe.from_user == current_user.id
    ).subquery()
    
    # Build query
    query = select(User).where(
        User.gender == opposite_gender,
        User.is_active == True,
        User.id != current_user.id,
        User.age.between(age_min, age_max),
        User.id.not_in(select(swiped_user_ids.c.to_user)),
    )
    
    # Distance filter (if user has location)
    if current_user.lat and current_user.lng:
        # Using PostgreSQL's earthdistance or simple calculation
        # For now, we'll filter in Python after query
        pass
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query)
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    users = result.scalars().all()
    
    # Build response with distances
    response_users = []
    for user in users:
        # Calculate distance
        distance = None
        if current_user.lat and current_user.lng and user.lat and user.lng:
            distance = calculate_distance(
                current_user.lat, current_user.lng,
                user.lat, user.lng
            )
            # Filter by distance if needed
            if distance and distance > distance_km:
                continue
        
        # Get main photo URL
        main_photo_url = None
        main_photo_query = select(Photo.url).where(
            Photo.user_id == user.id,
            Photo.is_main == True,
            Photo.status == "approved"
        )
        main_photo = await session.execute(main_photo_query)
        main_photo_url = main_photo.scalar_one_or_none()
        
        response_users.append(ProfileResponse(
            id=user.id,
            name=user.name,
            age=user.age,
            gender=user.gender,
            bio=user.bio,
            height=user.height,
            weight=user.weight,
            distance_km=round(distance, 1) if distance else None,
            main_photo_url=main_photo_url,
            is_premium=user.is_premium,
            is_verified=user.phone_verified,
        ))
    
    # Update total based on distance filter
    total = len(response_users) + offset
    
    return DiscoverResponse(
        users=response_users[:limit],
        next_offset=offset + limit if len(response_users) > limit else None,
        total=total,
    )