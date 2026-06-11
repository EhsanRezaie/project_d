from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


# User Management Schemas
class AdminUserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    age: int
    gender: str
    is_active: bool
    is_premium: bool
    premium_until: Optional[datetime] = None
    phone_verified: bool
    created_at: datetime
    last_seen_at: Optional[datetime] = None
    hide_last_seen: bool = False   
    hide_online_status: bool = False
    total_likes_sent: Optional[int] = None
    total_matches: Optional[int] = None
    total_messages: Optional[int] = None
    report_count: Optional[int] = None

    class Config:
        from_attributes = True


class AdminUserUpdate(BaseModel):
    is_active: Optional[bool] = None
    premium_until: Optional[datetime] = None


class AdminPremiumGrant(BaseModel):
    days: int = Field(..., ge=1, le=365)


class AdminUserListResponse(BaseModel):
    users: list[AdminUserResponse]
    total: int
    next_offset: Optional[int] = None


# Report Management Schemas
class AdminReportResponse(BaseModel):
    id: UUID
    reporter_id: UUID
    reporter_name: str
    reported_id: UUID
    reported_name: str
    reason: str
    status: str
    admin_note: Optional[str] = None
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminReportUpdate(BaseModel):
    status: str = Field(..., pattern="^(pending|reviewed|action_taken)$")
    admin_note: Optional[str] = Field(None, max_length=500)


# Ticket Management Schemas
class AdminTicketResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_name: str
    user_email: str
    subject: str
    message: str
    status: str
    admin_response: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AdminTicketUpdate(BaseModel):
    status: Optional[str] = Field(None, pattern="^(open|in_progress|closed)$")
    admin_response: Optional[str] = Field(None, max_length=2000)


# Photo Management Schemas
class AdminPhotoDetailResponse(BaseModel):
    id: UUID
    user_id: UUID
    user_name: str
    url: str
    is_main: bool
    status: str
    reject_reason: Optional[str] = None
    face_verified: bool
    order: int
    created_at: datetime

    class Config:
        from_attributes = True


# Message & Announcement Schemas - ADD THESE
class AdminMessageRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=2000)


class AdminMessageResponse(BaseModel):
    success: bool
    message: str
    user_id: UUID
    user_name: Optional[str] = None


class AdminAnnouncementRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=2000)
    to_premium_only: bool = False


class AdminAnnouncementResponse(BaseModel):
    success: bool
    message: str
    recipient_count: int