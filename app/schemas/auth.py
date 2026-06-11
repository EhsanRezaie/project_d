from uuid import UUID
from datetime import datetime
from typing import Optional
from app.schemas.user import UserResponse

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
    referral_code: Optional[str] = Field(None, max_length=20)

    @model_validator(mode="after")
    def password_not_whitespace(self) -> "RegisterRequest":
        if self.password.strip() == "":
            raise ValueError("Password cannot be whitespace only")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class GoogleAuthRequest(BaseModel):
    id_token: str


class RefreshRequest(BaseModel):
    refresh_token: str


class CompleteProfileRequest(BaseModel):
    age: int = Field(ge=18, le=100)
    gender: str = Field(pattern="^(male|female)$")
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)


# ---------------------------------------------------------------------------
# Response schemas - Import from user.py instead of duplicating
# ---------------------------------------------------------------------------
# UserResponse is now imported from user.py


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse