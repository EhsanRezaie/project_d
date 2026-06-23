# app/api/v1/endpoints/search.py
from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.dialects.postgresql import JSONB
from math import radians, sin, cos, sqrt, atan2
from datetime import datetime, timedelta, date

from app.db.session import get_session
from app.models.user import User
from app.models.user_profile import UserProfile
from app.models.user_interest import UserInterest
from app.models.interest import Interest
from app.models.photo import Photo
from app.models.block import Block
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.schemas.search import SearchProfileResponse, SearchResponse

router = APIRouter(prefix="/search", tags=["search"])


def calculate_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Calculate distance in km between two coordinates."""
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
    country: str = Query(None, max_length=100),
    province: str = Query(None, max_length=100),
    city: str = Query(None, max_length=100),
    religion: str = Query(None, max_length=50),
    ethnicity: str = Query(None, max_length=50),
    relationship_status: str = Query(None, max_length=50),
    body_type: str = Query(None, max_length=50),
    education: str = Query(None, max_length=50),
    smoking: str = Query(None, max_length=50),
    drinking: str = Query(None, max_length=50),
    political_orientation: str = Query(None, max_length=50),
    languages: str = Query(None, max_length=200),
    interests: str = Query(None, max_length=500),
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
    Users you blocked are excluded.
    """
    
    # Get current user's profile
    user_result = await session.execute(
        select(User)
        .options(
            selectinload(User.profile),
            selectinload(User.settings),
            selectinload(User.photos),
            selectinload(User.user_interests).selectinload(UserInterest.interest),
        )
        .where(User.id == current_user.id)
    )
    current_user_full = user_result.scalar_one_or_none()
    
    if not current_user_full or not current_user_full.profile:
        return SearchResponse(users=[], total=0, next_offset=None)
    
    current_profile = current_user_full.profile
    
    # Calculate birth date range from age
    today = date.today()
    
    # For age_min: max_birth_date = today - age_min years (youngest)
    # For age_max: min_birth_date = today - (age_max + 1) years (oldest)
    max_birth_date = today - timedelta(days=age_min * 365)
    min_birth_date = today - timedelta(days=(age_max + 1) * 365)
    
    # Users who YOU blocked
    blocked_user_ids = select(Block.blocked_id).where(Block.blocker_id == current_user.id)
    
    # Users who blocked YOU
    blocked_by_user_ids = select(Block.blocker_id).where(Block.blocked_id == current_user.id)
    
    # Base query with eager loading
    query = select(User).options(
        selectinload(User.profile),
        selectinload(User.settings),
        selectinload(User.photos),
        selectinload(User.user_interests).selectinload(UserInterest.interest),
    ).where(
        User.is_active == True,
        User.id != current_user.id,
        User.id.not_in(blocked_user_ids),      # ← Users you blocked
        User.id.not_in(blocked_by_user_ids),   # ← Users who blocked you
    )
    
    # Join with UserProfile for filtering
    query = query.join(UserProfile, User.id == UserProfile.user_id)
    
    # Filters
    query = query.where(UserProfile.birth_date.between(min_birth_date, max_birth_date))
    
    if gender:
        query = query.where(UserProfile.gender == gender)
    if height_min:
        query = query.where(UserProfile.height >= height_min)
    if height_max:
        query = query.where(UserProfile.height <= height_max)
    if weight_min:
        query = query.where(UserProfile.weight >= weight_min)
    if weight_max:
        query = query.where(UserProfile.weight <= weight_max)
    if is_verified is not None:
        query = query.where(UserProfile.is_verified == is_verified)
    if country:
        query = query.where(UserProfile.country == country)
    if province:
        query = query.where(UserProfile.province == province)
    if city:
        query = query.where(UserProfile.city == city)
    if religion:
        query = query.where(UserProfile.religion == religion)
    if ethnicity:
        query = query.where(UserProfile.ethnicity == ethnicity)
    if relationship_status:
        query = query.where(UserProfile.relationship_status == relationship_status)
    if body_type:
        query = query.where(UserProfile.body_type == body_type)
    if education:
        query = query.where(UserProfile.education == education)
    if smoking:
        query = query.where(UserProfile.smoking == smoking)
    if drinking:
        query = query.where(UserProfile.drinking == drinking)
    if political_orientation:
        query = query.where(UserProfile.political_orientation == political_orientation)
    
    # Languages filter (multi-value - AND condition)
    if languages:
        lang_list = [lang.strip() for lang in languages.split(",") if lang.strip()]
        if lang_list:
            query = query.where(
                UserProfile.languages.cast(JSONB).contains(lang_list)
            )
    
    # Interests filter (multi-value - AND condition)
    if interests:
        interest_list = [i.strip() for i in interests.split(",") if i.strip()]
        if interest_list:
            interest_count_subquery = (
                select(
                    UserInterest.user_id,
                    func.count(UserInterest.interest_id).label('match_count')
                )
                .join(Interest, UserInterest.interest_id == Interest.id)
                .where(Interest.name.in_(interest_list))
                .group_by(UserInterest.user_id)
                .having(func.count(UserInterest.interest_id) == len(interest_list))
                .subquery()
            )
            
            query = query.where(
                User.id.in_(
                    select(interest_count_subquery.c.user_id)
                )
            )
    
    # Has photos filter
    if has_photos is not None:
        if has_photos:
            query = query.where(
                select(func.count(Photo.id))
                .where(Photo.user_id == User.id, Photo.status == "approved")
                .as_scalar() > 0
            )
        else:
            query = query.where(
                select(func.count(Photo.id))
                .where(Photo.user_id == User.id, Photo.status == "approved")
                .as_scalar() == 0
            )
    
    # Execute query
    result = await session.execute(query)
    users = result.scalars().all()
    
    # Process users with distance calculation
    users_with_distance = []
    for user in users:
        if not user.profile:
            continue
            
        distance = None
        if distance_km and current_profile.lat and current_profile.lng and user.profile.lat and user.profile.lng:
            distance = calculate_distance(
                current_profile.lat, current_profile.lng,
                user.profile.lat, user.profile.lng
            )
            if distance > distance_km:
                continue
        
        # Get main photo URL
        main_photo_url = None
        if user.photos:
            main_photo = next((p for p in user.photos if p.is_main and p.status == "approved"), None)
            if main_photo:
                main_photo_url = main_photo.url
        
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
        users_with_distance.sort(key=lambda x: x["user"].profile.age, reverse=(sort_order == "desc"))
    elif sort_by == "name":
        users_with_distance.sort(key=lambda x: x["user"].profile.name if x["user"].profile else "", reverse=(sort_order == "desc"))
    
    # Pagination
    total = len(users_with_distance)
    paginated = users_with_distance[offset:offset + limit]
    
    # Build response with ALL fields
    response_users = []
    for item in paginated:
        user = item["user"]
        profile = user.profile
        settings = user.settings
        
        if not profile:
            continue
        
        hide_last_seen = settings.hide_last_seen if settings else False
        hide_online_status = settings.hide_online_status if settings else False
        
        # Get user interests
        user_interests = []
        if user.user_interests:
            user_interests = [ui.interest.name for ui in user.user_interests if ui.interest]
        
        response_users.append(SearchProfileResponse(
            id=user.id,
            name=profile.name,
            age=profile.age,  # ✅ Uses profile.age property
            gender=profile.gender,
            bio=profile.bio,
            height=profile.height,
            weight=profile.weight,
            body_type=profile.body_type,
            relationship_status=profile.relationship_status,
            living_situation=profile.living_situation,
            children_status=profile.children_status,
            smoking=profile.smoking,
            drinking=profile.drinking,
            education=profile.education,
            workplace=profile.workplace,
            religion=profile.religion,
            ethnicity=profile.ethnicity,
            political_orientation=profile.political_orientation,
            languages=profile.languages,
            country=profile.country,
            province=profile.province,
            city=profile.city,
            distance_km=round(item["distance"], 1) if item["distance"] and item["distance"] != 999999 else None,
            main_photo_url=item["main_photo_url"],
            is_premium=profile.is_premium,
            is_verified=profile.is_verified if profile.is_verified is not None else False,
            last_seen_at=user.last_seen_at.isoformat() if user.last_seen_at else None,
            hide_last_seen=hide_last_seen,
            hide_online_status=hide_online_status
        ))
    
    return SearchResponse(
        users=response_users,
        total=total,
        next_offset=offset + limit if offset + limit < total else None,
    )