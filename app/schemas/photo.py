from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PhotoResponse(BaseModel):
    """Response schema for photo"""
    id: UUID
    user_id: UUID
    url: str
    order: int
    is_main: bool
    status: str  # pending, approved, rejected
    reject_reason: Optional[str] = None
    face_verified: bool

    class Config:
        from_attributes = True


class PhotoUploadResponse(BaseModel):
    """Response after uploading a photo"""
    id: UUID
    url: str
    status: str
    message: str = "Photo uploaded. Under review by admin."


class PhotoUpdateOrderRequest(BaseModel):
    """Reorder photos"""
    orders: dict[UUID, int]  # photo_id -> new order


class AdminPhotoApproveRequest(BaseModel):
    """Admin approves photo"""
    photo_id: UUID


class AdminPhotoRejectRequest(BaseModel):
    """Admin rejects photo"""
    photo_id: UUID
    reason: str = Field(..., min_length=1, max_length=500)