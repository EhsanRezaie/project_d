from typing import Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from uuid import UUID


class UserResponse(BaseModel):
    """Response schema for user profile (excludes sensitive data)."""
    id: UUID
    email: str
    name: str
    age: int
    gender: str
    bio: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    is_premium: bool
    is_active: bool
    is_profile_complete: bool
    created_at: datetime
    last_seen_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserUpdateRequest(BaseModel):
    """Update user profile - all fields optional."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    age: Optional[int] = None
    gender: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None

    @field_validator("age")
    @classmethod
    def validate_age(cls, v: int) -> int:
        if v is not None and (v < 18 or v > 100):
            raise ValueError("Age must be between 18 and 100")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        if v is not None and v not in ["male", "female"]:
            raise ValueError("Gender must be 'male' or 'female'")
        return v

    @field_validator("height")
    @classmethod
    def validate_height(cls, v: int) -> int:
        if v is not None and (v < 50 or v > 250):
            raise ValueError("Height must be between 50cm and 250cm")
        return v

    @field_validator("weight")
    @classmethod
    def validate_weight(cls, v: int) -> int:
        if v is not None and (v < 30 or v > 300):
            raise ValueError("Weight must be between 30kg and 300kg")
        return v