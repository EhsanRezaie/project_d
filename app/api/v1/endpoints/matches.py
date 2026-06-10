from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from uuid import UUID

from app.db.session import get_session
from app.models.user import User
from app.models.match import Match
from app.models.photo import Photo
from app.models.message import Message
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.schemas.match import MatchResponse, MatchListResponse, MatchDetailResponse, MatchUserResponse, LastMessageResponse

router = APIRouter(prefix="/matches", tags=["matches"])


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


async def get_last_message(session: AsyncSession, match_id: UUID) -> dict | None:
    """Get last message for a match"""
    result = await session.execute(
        select(Message)
        .where(Message.match_id == match_id)
        .order_by(Message.sent_at.desc())
        .limit(1)
    )
    message = result.scalar_one_or_none()
    
    if message:
        return {
            "content": message.content,
            "sent_at": message.sent_at,
            "is_read": message.is_read
        }
    return None


@router.get("", response_model=MatchListResponse)
@limiter.limit("60/minute")
async def get_matches(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> MatchListResponse:
    """
    Get all active matches for current user.
    Returns matches sorted by most recent message or match date.
    """
    
    # Find all matches where current user is user1 or user2 - EAGER LOAD users
    query = select(Match).options(
        selectinload(Match.user1),
        selectinload(Match.user2)
    ).where(
        or_(
            Match.user1_id == current_user.id,
            Match.user2_id == current_user.id
        ),
        Match.is_active == True
    ).order_by(Match.matched_at.desc())
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total = await session.scalar(count_query)
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    result = await session.execute(query)
    matches = result.scalars().all()
    
    # Build response
    match_responses = []
    for match in matches:
        # Get the other user
        if match.user1_id == current_user.id:
            other_user = match.user2
        else:
            other_user = match.user1
        
        # Get other user's main photo (separate query to avoid complexity)
        main_photo_url = await get_user_main_photo_url(session, other_user.id)
        
        # Get last message
        last_message = await get_last_message(session, match.id)
        
        match_responses.append(MatchResponse(
            id=match.id,
            matched_at=match.matched_at,
            user=MatchUserResponse(
                id=other_user.id,
                name=other_user.name,
                age=other_user.age,
                main_photo_url=main_photo_url,
            ),
            last_message=LastMessageResponse(
                content=last_message["content"],
                sent_at=last_message["sent_at"],
                is_read=last_message["is_read"]
            ) if last_message else None
        ))
    
    return MatchListResponse(
        matches=match_responses,
        total=total or 0
    )


@router.get("/{match_id}", response_model=MatchDetailResponse)
@limiter.limit("60/minute")
async def get_match_detail(
    request: Request,
    match_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> MatchDetailResponse:
    """
    Get detailed information about a specific match.
    """
    
    query = select(Match).options(
        selectinload(Match.user1),
        selectinload(Match.user2)
    ).where(
        Match.id == match_id,
        Match.is_active == True,
        or_(
            Match.user1_id == current_user.id,
            Match.user2_id == current_user.id
        )
    )
    
    result = await session.execute(query)
    match = result.scalar_one_or_none()
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Match not found"
        )
    
    # Get both users' main photos
    user1_photo = await get_user_main_photo_url(session, match.user1_id)
    user2_photo = await get_user_main_photo_url(session, match.user2_id)
    
    return MatchDetailResponse(
        id=match.id,
        matched_at=match.matched_at,
        user1=MatchUserResponse(
            id=match.user1.id,
            name=match.user1.name,
            age=match.user1.age,
            main_photo_url=user1_photo,
        ),
        user2=MatchUserResponse(
            id=match.user2.id,
            name=match.user2.name,
            age=match.user2.age,
            main_photo_url=user2_photo,
        ),
        is_active=match.is_active
    )