from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel, Field


class SearchProfileResponse(BaseModel):
    """Response schema for search results"""
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
    is_verified: bool
    last_seen_at: Optional[str] = None
    
    class Config:
        from_attributes = True


class SearchResponse(BaseModel):
    """Response for search endpoint"""
    users: List[SearchProfileResponse]
    total: int
    next_offset: Optional[int] = None


class SearchFilters(BaseModel):
    """Search filters"""
    age_min: int = Field(18, ge=18, le=100)
    age_max: int = Field(100, ge=18, le=100)
    distance_km: Optional[int] = Field(None, ge=1, le=500)
    gender: Optional[str] = Field(None, pattern="^(male|female)$")
    height_min: Optional[int] = Field(None, ge=50, le=250)
    height_max: Optional[int] = Field(None, ge=50, le=250)
    weight_min: Optional[int] = Field(None, ge=30, le=300)
    weight_max: Optional[int] = Field(None, ge=30, le=300)
    has_photos: Optional[bool] = None
    is_verified: Optional[bool] = None
    province: Optional[str] = Field(None, max_length=100)  # ADD THIS
    city: Optional[str] = Field(None, max_length=100)      # ADD THIS
    sort_by: str = Field("recent", pattern="^(recent|distance|age|name)$")
    sort_order: str = Field("desc", pattern="^(asc|desc)$")
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class BlockResponse(BaseModel):
    """Response for block list"""
    id: UUID
    blocked_user_id: UUID
    blocked_user_name: str
    blocked_at: str