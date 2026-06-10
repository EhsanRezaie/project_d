from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import date
from uuid import UUID

from app.db.session import get_session
from app.models.user import User
from app.models.swipe import Swipe
from app.models.match import Match
from app.models.daily_limit import DailyLimit
from app.models.photo import Photo
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.schemas.discover import SwipeRequest, SwipeResponse
from app.services.websocket_manager import websocket_manager

router = APIRouter(prefix="/swipes", tags=["swipes"])


async def get_or_create_daily_limit(
    session: AsyncSession, 
    user_id: UUID, 
    target_date: date
) -> DailyLimit:
    """Get or create daily limit record for a user on a specific date"""
    result = await session.execute(
        select(DailyLimit).where(
            DailyLimit.user_id == user_id,
            DailyLimit.date == target_date
        )
    )
    daily_limit = result.scalar_one_or_none()
    
    if not daily_limit:
        daily_limit = DailyLimit(
            user_id=user_id,
            date=target_date,
            likes_used=0,
            chats_used=0,
            ad_likes_bonus=0,
            ad_chats_bonus=0,
        )
        session.add(daily_limit)
        await session.flush()
    
    return daily_limit


async def get_user_main_photo_url(session: AsyncSession, user_id: UUID) -> str | None:
    """Get user's main approved photo URL"""
    result = await session.execute(
        select(Photo.url).where(
            Photo.user_id == user_id,
            Photo.is_main == True,
            Photo.status == "approved"
        )
    )
    return result.scalar_one_or_none()


@router.post("", response_model=SwipeResponse)
@limiter.limit("30/minute")
async def swipe(
    request: Request,
    body: SwipeRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SwipeResponse:
    """
    Swipe right (like) or left (pass) on a user.
    
    Rules:
    1. Cannot swipe on yourself
    2. Cannot swipe twice on same user
    3. Free users: max 50 likes per day
    4. If both like each other → create match
    """
    
    # Cannot swipe on yourself
    if body.user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot swipe on yourself"
        )
    
    # Check if target user exists and is active
    result = await session.execute(
        select(User).where(
            User.id == body.user_id,
            User.is_active == True
        )
    )
    target_user = result.scalar_one_or_none()
    
    if not target_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already swiped
    existing_result = await session.execute(
        select(Swipe).where(
            Swipe.from_user == current_user.id,
            Swipe.to_user == body.user_id
        )
    )
    existing_swipe = existing_result.scalar_one_or_none()
    
    if existing_swipe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Already swiped {existing_swipe.direction} on this user"
        )
    
    # Check daily like limit (only for 'like' direction)
    likes_remaining = None
    if body.direction == "like" and not current_user.is_premium:
        today = date.today()
        daily_limit = await get_or_create_daily_limit(session, current_user.id, today)
        
        # Available likes = 50 (base) + bonus from ads - used
        available_likes = 50 + daily_limit.ad_likes_bonus - daily_limit.likes_used
        
        if available_likes <= 0:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Daily like limit reached. Watch an ad or upgrade to premium."
            )
        
        likes_remaining = available_likes - 1
        
        # Increment used likes
        daily_limit.likes_used += 1
        session.add(daily_limit)
    
    # Create swipe record
    new_swipe = Swipe(
        from_user=current_user.id,
        to_user=body.user_id,
        direction=body.direction,
    )
    session.add(new_swipe)
    await session.flush()
    
    # Check for match (if both liked each other)
    matched = False
    match_id = None
    
    if body.direction == "like":
        # Check if target user liked current user
        mutual_result = await session.execute(
            select(Swipe).where(
                Swipe.from_user == body.user_id,
                Swipe.to_user == current_user.id,
                Swipe.direction == "like"
            )
        )
        mutual_swipe = mutual_result.scalar_one_or_none()
        
        if mutual_swipe:
            # Create match
            new_match = Match(
                user1_id=current_user.id,
                user2_id=body.user_id,
                is_active=True,
            )
            session.add(new_match)
            await session.flush()
            
            matched = True
            match_id = new_match.id
            
            # Send WebSocket notification to both users
            user1_data = {
                "id": str(current_user.id),
                "name": current_user.name,
                "age": current_user.age,
                "main_photo_url": await get_user_main_photo_url(session, current_user.id),
            }
            
            user2_data = {
                "id": str(target_user.id),
                "name": target_user.name,
                "age": target_user.age,
                "main_photo_url": await get_user_main_photo_url(session, target_user.id),
            }
            
            await websocket_manager.broadcast_match(
                str(current_user.id),
                str(target_user.id),
                str(new_match.id),
                user1_data,
                user2_data
            )
    
    await session.commit()
    
    return SwipeResponse(
        matched=matched,
        match_id=match_id,
        likes_remaining_today=likes_remaining,
        message="Swiped successfully" + (" You matched!" if matched else "")
    )


@router.get("/stats")
@limiter.limit("30/minute")
async def get_swipe_stats(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Get swipe statistics for current user"""
    
    # Total swipes today
    today = date.today()
    daily_limit = await get_or_create_daily_limit(session, current_user.id, today)
    
    available_likes = 50 + daily_limit.ad_likes_bonus - daily_limit.likes_used
    if current_user.is_premium:
        available_likes = -1  # Unlimited
    
    # Count total likes sent
    total_likes_result = await session.execute(
        select(func.count()).where(
            Swipe.from_user == current_user.id,
            Swipe.direction == "like"
        )
    )
    total_likes = total_likes_result.scalar()
    
    # Count total passes sent
    total_passes_result = await session.execute(
        select(func.count()).where(
            Swipe.from_user == current_user.id,
            Swipe.direction == "pass"
        )
    )
    total_passes = total_passes_result.scalar()
    
    # Count matches
    matches_result = await session.execute(
        select(func.count()).where(
            or_(
                Match.user1_id == current_user.id,
                Match.user2_id == current_user.id
            ),
            Match.is_active == True
        )
    )
    total_matches = matches_result.scalar()
    
    return {
        "daily_likes_remaining": available_likes if available_likes > 0 else 0,
        "is_unlimited": current_user.is_premium,
        "total_likes_sent": total_likes,
        "total_passes_sent": total_passes,
        "total_matches": total_matches,
    }