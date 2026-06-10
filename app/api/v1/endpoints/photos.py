from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from uuid import UUID

from app.db.session import get_session
from app.models.user import User
from app.models.photo import Photo
from app.core.deps import get_current_user
from app.core.limiter import limiter
from app.services.photo_service import PhotoService
from app.schemas.photo import PhotoResponse, PhotoUploadResponse

router = APIRouter(prefix="/users/me/photos", tags=["photos"])


@router.post("", response_model=PhotoUploadResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def upload_photo(
    request: Request,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PhotoUploadResponse:
    """
    Upload a profile photo.
    Photo is saved with status='pending' and must be approved by admin.
    """
    # Read file data
    file_data = await file.read()
    
    # Validate image
    is_valid, error = await PhotoService.validate_image(file_data, file.filename)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error,
        )
    
    # Check photo limit (max 6 photos)
    result = await session.execute(
        select(Photo).where(Photo.user_id == current_user.id)
    )
    photos = result.scalars().all()
    if len(photos) >= 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 6 photos per user",
        )
    
    # Create photo record
    new_photo = Photo(
        user_id=current_user.id,
        url="",  # Will update after save
        order=len(photos),
        is_main=len(photos) == 0,  # First photo becomes main
        status="pending",
    )
    session.add(new_photo)
    await session.flush()  # Get ID
    
    # Save file to disk
    photo_url = await PhotoService.save_photo(
        str(current_user.id),
        str(new_photo.id),
        file_data,
    )
    
    # Update URL
    new_photo.url = photo_url
    await session.commit()
    await session.refresh(new_photo)
    
    return PhotoUploadResponse(
        id=new_photo.id,
        url=photo_url,
        status="pending",
        message="Photo uploaded. Under review by admin.",
    )


@router.get("", response_model=list[PhotoResponse])
@limiter.limit("30/minute")
async def get_my_photos(
    request: Request,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[PhotoResponse]:
    """
    Get all photos for current user.
    Shows all photos (pending, approved, rejected).
    """
    result = await session.execute(
        select(Photo)
        .where(Photo.user_id == current_user.id)
        .order_by(Photo.order)
    )
    photos = result.scalars().all()
    return [PhotoResponse.model_validate(p) for p in photos]


@router.delete("/{photo_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def delete_photo(
    request: Request,
    photo_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> None:
    """
    Delete a photo.
    """
    # Find photo
    result = await session.execute(
        select(Photo).where(
            Photo.id == photo_id,
            Photo.user_id == current_user.id,
        )
    )
    photo = result.scalar_one_or_none()
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found",
        )
    
    # Delete from disk
    await PhotoService.delete_photo(str(current_user.id), str(photo_id))
    
    # Delete from database
    await session.delete(photo)
    await session.commit()
    
    # If deleted photo was main, set new main photo
    if photo.is_main:
        result = await session.execute(
            select(Photo)
            .where(Photo.user_id == current_user.id)
            .order_by(Photo.order)
            .limit(1)
        )
        first_photo = result.scalar_one_or_none()
        if first_photo:
            first_photo.is_main = True
            await session.commit()


@router.put("/{photo_id}/main", response_model=PhotoResponse)
@limiter.limit("20/minute")
async def set_main_photo(
    request: Request,
    photo_id: UUID,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> PhotoResponse:
    """
    Set a photo as main profile photo.
    """
    # Find the photo to set as main
    result = await session.execute(
        select(Photo).where(
            Photo.id == photo_id,
            Photo.user_id == current_user.id,
        )
    )
    photo = result.scalar_one_or_none()
    
    if not photo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Photo not found",
        )
    
    if photo.status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only approved photos can be set as main",
        )
    
    # Remove main flag from all photos
    await session.execute(
        update(Photo)
        .where(Photo.user_id == current_user.id)
        .values(is_main=False)
    )
    
    # Set new main photo
    photo.is_main = True
    await session.commit()
    await session.refresh(photo)
    
    return PhotoResponse.model_validate(photo)