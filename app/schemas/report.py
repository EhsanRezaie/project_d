from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class ReportRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=500)


class ReportResponse(BaseModel):
    id: UUID
    reported_user_id: UUID
    reason: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True