from uuid import UUID
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: UUID
    type: str
    title: str
    body: Optional[str] = None
    data: Optional[dict] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


class MarkReadRequest(BaseModel):
    notification_ids: List[UUID]


class NotificationListResponse(BaseModel):
    notifications: List[NotificationResponse]
    total: int
    next_offset: Optional[int] = None