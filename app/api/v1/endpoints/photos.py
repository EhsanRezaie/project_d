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


async def _to_photo_response(photo: Photo) -> PhotoResponse:
    """
    Build a PhotoResponse with a real, loadable URL.

    Photo.url stores a bare object KEY (e.g. "users/<id>/<photo_id>.jpg"),
    not a usable URL — PhotoService.get_photo_url() resolves it based on
    moderation status: public URL if approved, short-lived signed URL
    otherwise (so owners can still see their own pending/rejected photos).
    """
    resolved_url = await PhotoService.get_photo_url(photo.url, photo.status)
    return PhotoResponse(
        id=photo.id,
        user_id=photo.user_id,
        url=resolved_url,
        order=photo.order,
        is_main=photo.is_main,
        status=photo.status,
        reject_reason=photo.reject_reason,
        face_verified=photo.face_verified,
    )


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
    New uploads are stored in the private bucket — not publicly visible
    until approved (see app/services/photo_service.py + admin_photos.py).
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

    # Upload to object storage (private bucket) — returns the object KEY,
    # not a loadable URL. See PhotoService.save_photo().
    photo_key = await PhotoService.save_photo(
        str(current_user.id),
        str(new_photo.id),
        file_data,
    )

    # Store the key
    new_photo.url = photo_key
    await session.commit()
    await session.refresh(new_photo)

    # Resolve a real, loadable (signed) URL for the immediate upload response
    display_url = await PhotoService.get_photo_url(photo_key, new_photo.status)

    return PhotoUploadResponse(
        id=new_photo.id,
        url=display_url,
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
    Shows all photos (pending, approved, rejected) — pending/rejected
    photos resolve to short-lived signed URLs so the owner can still
    view them (e.g. to see why a photo was rejected); approved photos
    resolve to plain public URLs.
    """
    result = await session.execute(
        select(Photo)
        .where(Photo.user_id == current_user.id)
        .order_by(Photo.order)
    )
    photos = result.scalars().all()
    return [await _to_photo_response(p) for p in photos]


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

    # Delete from object storage (checks both buckets, since the photo
    # could be in either depending on its moderation status)
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

    return await _to_photo_response(photo)