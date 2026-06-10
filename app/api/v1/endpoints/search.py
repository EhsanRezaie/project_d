from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from math import radians, sin, cos, sqrt, atan2

from app.db.session import get_session
from app.models.user import User
from app.models.photo import Photo
from app.models.block import Block
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.schemas.search import SearchProfileResponse, SearchResponse, SearchFilters

router = APIRouter(prefix="/search", tags=["search"])


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in km between two coordinates"""
    if not lat1 or not lng1 or not lat2 or not lng2:
        return None
    
    R = 6371
    lat1_rad = radians(lat1)
    lat2_rad = radians(lat2)
    delta_lat = radians(lat2 - lat1)
    delta_lng = radians(lng2 - lng1)
    
    a = sin(delta_lat / 2) ** 2 + cos(lat1_rad) * cos(lat2_rad) * sin(delta_lng / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c


@router.get("", response_model=SearchResponse)
@limiter.limit("60/minute")
async def search_users(
    request: Request,
    age_min: int = Query(18, ge=18, le=100),
    age_max: int = Query(100, ge=18, le=100),
    distance_km: int = Query(None, ge=1, le=500),
    gender: str = Query(None, pattern="^(male|female)$"),
    height_min: int = Query(None, ge=50, le=250),
    height_max: int = Query(None, ge=50, le=250),
    weight_min: int = Query(None, ge=30, le=300),
    weight_max: int = Query(None, ge=30, le=300),
    has_photos: bool = Query(None),
    is_verified: bool = Query(None),
    sort_by: str = Query("recent", pattern="^(recent|distance|age|name)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SearchResponse:
    """
    Search users with advanced filters.
    Users who blocked you are excluded.
    """
    
    # Base query - exclude self and blocked users
    blocked_user_ids = select(Block.blocked_id).where(Block.blocker_id == current_user.id)
    
    query = select(User).where(
        User.is_active == True,
        User.id != current_user.id,
        User.id.not_in(blocked_user_ids),
    )
    
    # Gender filter (optional)
    if gender:
        query = query.where(User.gender == gender)
    
    # Age filter
    query = query.where(User.age.between(age_min, age_max))
    
    # Height filter
    if height_min:
        query = query.where(User.height >= height_min)
    if height_max:
        query = query.where(User.height <= height_max)
    
    # Weight filter
    if weight_min:
        query = query.where(User.weight >= weight_min)
    if weight_max:
        query = query.where(User.weight <= weight_max)
    
    # Phone verified filter
    if is_verified is not None:
        query = query.where(User.phone_verified == is_verified)
    
    # Has photos filter
    if has_photos is not None:
        if has_photos:
            query = query.where(User.photos.any(Photo.status == "approved"))
        else:
            query = query.where(~User.photos.any(Photo.status == "approved"))
    
    # Get all users first (for distance calculation)
    result = await session.execute(query)
    users = result.scalars().all()
    
    # Filter by distance and calculate distances
    users_with_distance = []
    for user in users:
        distance = None
        if distance_km and current_user.lat and current_user.lng and user.lat and user.lng:
            distance = calculate_distance(
                current_user.lat, current_user.lng,
                user.lat, user.lng
            )
            if distance > distance_km:
                continue
        else:
            distance = 999999  # Far away for sorting
        
        # Get main photo URL
        main_photo_url = None
        main_photo_query = select(Photo.url).where(
            Photo.user_id == user.id,
            Photo.is_main == True,
            Photo.status == "approved"
        )
        main_photo = await session.execute(main_photo_query)
        main_photo_url = main_photo.scalar_one_or_none()
        
        users_with_distance.append({
            "user": user,
            "distance": distance,
            "main_photo_url": main_photo_url,
        })
    
    # Sorting
    if sort_by == "recent":
        users_with_distance.sort(key=lambda x: x["user"].created_at, reverse=(sort_order == "desc"))
    elif sort_by == "distance":
        users_with_distance.sort(key=lambda x: x["distance"] if x["distance"] else 999999)
    elif sort_by == "age":
        users_with_distance.sort(key=lambda x: x["user"].age, reverse=(sort_order == "desc"))
    elif sort_by == "name":
        users_with_distance.sort(key=lambda x: x["user"].name, reverse=(sort_order == "desc"))
    
    # Pagination
    total = len(users_with_distance)
    paginated = users_with_distance[offset:offset + limit]
    
    response_users = []
    for item in paginated:
        user = item["user"]
        response_users.append(SearchProfileResponse(
            id=user.id,
            name=user.name,
            age=user.age,
            gender=user.gender,
            bio=user.bio,
            height=user.height,
            weight=user.weight,
            distance_km=round(item["distance"], 1) if item["distance"] and item["distance"] != 999999 else None,
            main_photo_url=item["main_photo_url"],
            is_premium=user.is_premium,
            is_verified=user.phone_verified,
            last_seen_at=user.last_seen_at.isoformat() if user.last_seen_at else None,
        ))
    
    return SearchResponse(
        users=response_users,
        total=total,
        next_offset=offset + limit if offset + limit < total else None,
    )