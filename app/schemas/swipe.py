from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID
from enum import Enum


class SwipeDirection(str, Enum):
    like = "like"
    pass_ = "pass"


class SwipeRequest(BaseModel):
    """Request schema for swiping on a user."""
    direction: SwipeDirection


class SwipeResponse(BaseModel):
    """Response schema for swipe action."""
    id: UUID
    from_user: UUID
    to_user: UUID
    direction: str
    is_match: bool = False
    match_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class SwipeStatsResponse(BaseModel):
    """Response schema for swipe statistics."""
    total_likes: int = 0
    total_passes: int = 0
    likes_today: int = 0
    likes_remaining: int = 0
    matches_today: int = 0
    is_premium: bool = False
    likes_limit: int = 20
    chats_limit: int = 10
    likes_used_today: int = 0
    chats_used_today: int = 0
    ad_likes_bonus: int = 0
    ad_chats_bonus: int = 0

    class Config:
        from_attributes = True


class SwipeHistoryResponse(BaseModel):
    """Response schema for swipe history."""
    id: UUID
    from_user: UUID
    to_user: UUID
    to_user_name: Optional[str] = None
    direction: str
    created_at: datetime

    class Config:
        from_attributes = True


class SwipeListResponse(BaseModel):
    """Response schema for list of swipes."""
    items: List[SwipeHistoryResponse]
    total: int
    page: int
    limit: int
    has_next: bool

    class Config:
        from_attributes = True