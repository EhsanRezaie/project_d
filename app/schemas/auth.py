from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import date, datetime
from uuid import UUID
from enum import Enum


# ============ Enums ============

class Gender(str, Enum):
    male = "male"
    female = "female"


class SexualOrientation(str, Enum):
    straight = "straight"
    gay = "gay"
    bisexual = "bisexual"
    pansexual = "pansexual"
    asexual = "asexual"


class BodyType(str, Enum):
    slim = "slim"
    average = "average"
    athletic = "athletic"
    curvy = "curvy"
    muscular = "muscular"
    overweight = "overweight"


class RelationshipStatus(str, Enum):
    single = "single"
    divorced = "divorced"
    widowed = "widowed"
    separated = "separated"


class LivingSituation(str, Enum):
    alone = "alone"
    with_family = "with_family"
    with_roommate = "with_roommate"
    with_partner = "with_partner"


class ChildrenStatus(str, Enum):
    have = "have"
    dont_have = "dont_have"
    want = "want"
    dont_want = "dont_want"


class SmokingStatus(str, Enum):
    never = "never"
    occasionally = "occasionally"
    regularly = "regularly"


class DrinkingStatus(str, Enum):
    never = "never"
    socially = "socially"
    regularly = "regularly"


class EducationLevel(str, Enum):
    high_school = "high_school"
    bachelor = "bachelor"
    master = "master"
    phd = "phd"


class PoliticalOrientation(str, Enum):
    liberal = "liberal"
    conservative = "conservative"
    moderate = "moderate"
    apolitical = "apolitical"


# ============ Step 1: Register Init ============

class RegisterInitRequest(BaseModel):
    email: EmailStr


class RegisterInitResponse(BaseModel):
    message: str = "Verification code sent to your email"
    email: str
    expires_in: int = 300


# ============ Step 2: Register Verify ============

class RegisterVerifyRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6, description="6-digit verification code")
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    referral_code: Optional[str] = Field(None, min_length=8, max_length=8, description="Optional referral code")


class RegisterVerifyResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: UUID


# ============ Step 3: Onboarding Complete ============

class UserPromptCreateRequest(BaseModel):
    prompt_id: UUID
    answer: str = Field(..., max_length=500)


class OnboardingCompleteRequest(BaseModel):
    """Complete user profile after email verification."""
    # Identity
    name: str = Field(..., min_length=2, max_length=100)
    birth_date: date
    gender: Gender
    sexual_orientation: Optional[SexualOrientation] = None
    bio: Optional[str] = Field(None, max_length=500)
    
    # Appearance
    height: Optional[int] = Field(None, ge=50, le=250, description="Height in cm")
    weight: Optional[int] = Field(None, ge=30, le=300, description="Weight in kg")
    body_type: Optional[BodyType] = None
    
    # Lifestyle
    relationship_status: Optional[RelationshipStatus] = None
    living_situation: Optional[LivingSituation] = None
    children_status: Optional[ChildrenStatus] = None
    smoking: Optional[SmokingStatus] = None
    drinking: Optional[DrinkingStatus] = None
    
    # Background
    education: Optional[EducationLevel] = None
    workplace: Optional[str] = Field(None, max_length=100)
    religion: Optional[str] = Field(None, max_length=50)
    ethnicity: Optional[str] = Field(None, max_length=50)
    political_orientation: Optional[PoliticalOrientation] = None
    languages: Optional[List[str]] = None
    
    # Location (required)
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    country: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)
    
    # Optional extras
    interests: Optional[List[str]] = Field(None, description="List of interest names")
    prompts: Optional[List[UserPromptCreateRequest]] = None

    @field_validator("gender", mode="before")
    @classmethod
    def validate_gender(cls, v):
        if isinstance(v, Gender):
            return v.value
        return v


# ============ Login ============

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: "UserProfileResponse"


# ============ Refresh Token ============

class RefreshTokenRequest(BaseModel):
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


# ============ Google Login ============

class GoogleLoginRequest(BaseModel):
    id_token: str
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    picture: Optional[str] = None


# ============ Logout ============

class LogoutRequest(BaseModel):
    refresh_token: str


# ============ Password Reset ============

class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetVerifyRequest(BaseModel):
    email: EmailStr
    code: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=8)


# ============ Change Password ============

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str = Field(..., min_length=8)


# ============ Forward References ============

# Import here to avoid circular import
from app.schemas.user import UserProfileResponse
LoginResponse.model_rebuild()