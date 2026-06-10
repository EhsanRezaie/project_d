from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class ProfileResponse(BaseModel):
    """Response schema for user profile in discover/search"""
    id: UUID
    name: str
    age: int
    gender: str
    bio: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    distance_km: Optional[float] = None
    main_photo_url: Optional[str] = None
    is_premium: bool
    is_verified: bool  # phone_verified
    
    class Config:
        from_attributes = True


class DiscoverResponse(BaseModel):
    """Response for discover endpoint"""
    users: List[ProfileResponse]
    next_offset: Optional[int] = None
    total: int


class SwipeRequest(BaseModel):
    """Request for swipe endpoint"""
    user_id: UUID
    direction: str  # 'like' or 'pass'


class SwipeResponse(BaseModel):
    """Response for swipe endpoint"""
    matched: bool
    match_id: Optional[UUID] = None
    likes_remaining_today: Optional[int] = None
    message: str