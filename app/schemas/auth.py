from uuid import UUID
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, model_validator


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(ge=18, le=100)
    gender: str = Field(pattern="^(male|female)$")

    @model_validator(mode="after")
    def password_not_whitespace(self) -> "RegisterRequest":
        if self.password.strip() == "":
            raise ValueError("Password cannot be whitespace only")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    """Client sends the ID token it received from Google Sign-In."""
    id_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class UserResponse(BaseModel):
    id: UUID
    email: str
    name: str
    age: int
    gender: str
    bio: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    phone_verified: bool
    is_premium: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse