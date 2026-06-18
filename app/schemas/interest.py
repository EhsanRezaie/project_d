from typing import Optional
from pydantic import BaseModel
from uuid import UUID


class InterestResponse(BaseModel):
    id: UUID
    name: str
    category: Optional[str] = None
    icon: Optional[str] = None

    class Config:
        from_attributes = True


class InterestCreateRequest(BaseModel):
    name: str
    category: Optional[str] = None
    icon: Optional[str] = None


class UserInterestResponse(BaseModel):
    id: UUID
    interest_id: UUID
    name: str
    category: Optional[str] = None
    icon: Optional[str] = None

    class Config:
        from_attributes = True