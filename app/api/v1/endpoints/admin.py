from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID

from app.db.session import get_session
from app.models.photo import Photo
from app.models.user import User
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger("admin")

router = APIRouter(prefix="/admin", tags=["admin"])


# Simple admin check - for MVP, use a secret key
# In production, implement proper admin authentication
async def verify_admin(request: Request) -> bool:
    """Verify admin access via X-Admin-Key header"""
    admin_key = request.headers.get("X-Admin-Key")
    if not settings.ADMIN_SECRET_KEY:
        logger.error("ADMIN_SECRET_KEY not configured in .env")
        return False
    return admin_key == settings.ADMIN_SECRET_KEY


@router.get("/photos/pending")
async def get_pending_photos(
    request: Request,
    session: AsyncSession = Depends(get_session),
    limit: int = 50,
) -> list[dict]:
    """
    Get all pending photos for admin review.
    Requires X-Admin-Key header.
    
    Returns list of pending photos with user info.
    """
    if not await verify_admin(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin key",
        )
    
    # Query pending photos with user info
    result = await session.execute(
        select(Photo, User)
        .join(User, Photo.user_id == User.id)
        .where(Photo.status == "pending")
        .order_by(Photo.created_at)
        .limit(limit)
    )
    
    photos = []
    for photo, user in result:
        photos.append({
            "photo_id": str(photo.id),
            "user_id": str(user.id),
            "user_name": user.name,
            "user_email": user.email,
            "url": photo.url,
            "order": photo.order,
            "is_main": photo.is_main,
            "uploaded_at": photo.created_at.isoformat() if photo.created_at else None,
        })
    
    logger.info(f"Admin retrieved {len(photos)} pending photos")
    
    return photos


@router.post("/photos/{photo_id}/approve")
async def approve_photo(
    request: Request,
    photo_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Approve a pending photo.
    Requires X-Admin-Key header.
    
    After approval, photo becomes visible to other users.
    """
    if not await verify_admin(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin key",
        )
    
    # Find the photo
    result = await session.execute(
        select(Photo).where(Photo.id == photo_id)
    )
    photo = result.scalar_one_or_none()
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found",
        )
    
    if photo.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Photo already {photo.status}. Cannot approve.",
        )
    
    # Approve the photo
    photo.status = "approved"
    await session.commit()
    
    logger.info(f"Admin approved photo {photo_id} for user {photo.user_id}")
    
    return {
        "message": "Photo approved successfully",
        "photo_id": str(photo_id),
        "status": "approved"
    }


@router.post("/photos/{photo_id}/reject")
async def reject_photo(
    request: Request,
    photo_id: UUID,
    reason: str,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Reject a pending photo with reason.
    Requires X-Admin-Key header.
    
    User will see the rejection reason in their photo list.
    """
    if not await verify_admin(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin key",
        )
    
    # Validate reason
    if not reason or len(reason.strip()) < 1:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejection reason is required",
        )
    
    if len(reason) > 500:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rejection reason too long (max 500 characters)",
        )
    
    # Find the photo
    result = await session.execute(
        select(Photo).where(Photo.id == photo_id)
    )
    photo = result.scalar_one_or_none()
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found",
        )
    
    if photo.status != "pending":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Photo already {photo.status}. Cannot reject.",
        )
    
    # Reject the photo
    photo.status = "rejected"
    photo.reject_reason = reason
    await session.commit()
    
    logger.info(f"Admin rejected photo {photo_id} for user {photo.user_id}: {reason}")
    
    return {
        "message": "Photo rejected successfully",
        "photo_id": str(photo_id),
        "status": "rejected",
        "reason": reason
    }


@router.get("/photos/stats")
async def get_photo_stats(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Get photo moderation statistics.
    Requires X-Admin-Key header.
    """
    if not await verify_admin(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin key",
        )
    
    # Count photos by status
    from sqlalchemy import func
    
    result = await session.execute(
        select(Photo.status, func.count(Photo.id))
        .group_by(Photo.status)
    )
    
    stats = {status: count for status, count in result.all()}
    
    # Get total users with photos
    result = await session.execute(
        select(func.count(func.distinct(Photo.user_id)))
    )
    users_with_photos = result.scalar_one()
    
    logger.info("Admin retrieved photo statistics")
    
    return {
        "pending": stats.get("pending", 0),
        "approved": stats.get("approved", 0),
        "rejected": stats.get("rejected", 0),
        "total_photos": sum(stats.values()),
        "users_with_photos": users_with_photos,
    }


@router.get("/photos/user/{user_id}")
async def get_user_photos_for_admin(
    request: Request,
    user_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """
    Get all photos for a specific user (admin view).
    Requires X-Admin-Key header.
    """
    if not await verify_admin(request):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin key",
        )
    
    # Get user
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    # Get user's photos
    result = await session.execute(
        select(Photo)
        .where(Photo.user_id == user_id)
        .order_by(Photo.order)
    )
    photos = result.scalars().all()
    
    logger.info(f"Admin retrieved {len(photos)} photos for user {user_id}")
    
    return [
        {
            "photo_id": str(photo.id),
            "url": photo.url,
            "order": photo.order,
            "is_main": photo.is_main,
            "status": photo.status,
            "reject_reason": photo.reject_reason,
            "face_verified": photo.face_verified,
            "uploaded_at": photo.created_at.isoformat() if photo.created_at else None,
        }
        for photo in photos
    ]