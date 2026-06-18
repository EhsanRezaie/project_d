from typing import Optional, List
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from uuid import UUID


# ============ Request Schemas ============

class UserUpdateRequest(BaseModel):
    """Update user profile - all fields optional."""
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    gender: Optional[str] = None
    sexual_orientation: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    body_type: Optional[str] = None
    relationship_status: Optional[str] = None
    living_situation: Optional[str] = None
    children_status: Optional[str] = None
    smoking: Optional[str] = None
    drinking: Optional[str] = None
    education: Optional[str] = None
    workplace: Optional[str] = None
    religion: Optional[str] = None
    ethnicity: Optional[str] = None
    political_orientation: Optional[str] = None

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str) -> str:
        if v is not None and v not in ["male", "female"]:
            raise ValueError("Gender must be 'male' or 'female'")
        return v

    @field_validator("sexual_orientation")
    @classmethod
    def validate_sexual_orientation(cls, v: str) -> str:
        if v is not None and v not in ["straight", "gay", "bisexual", "pansexual", "asexual"]:
            raise ValueError("Invalid sexual orientation")
        return v

    @field_validator("body_type")
    @classmethod
    def validate_body_type(cls, v: str) -> str:
        if v is not None and v not in ["slim", "average", "athletic", "curvy", "muscular", "overweight"]:
            raise ValueError("Invalid body type")
        return v

    @field_validator("relationship_status")
    @classmethod
    def validate_relationship_status(cls, v: str) -> str:
        if v is not None and v not in ["single", "divorced", "widowed", "separated"]:
            raise ValueError("Invalid relationship status")
        return v

    @field_validator("living_situation")
    @classmethod
    def validate_living_situation(cls, v: str) -> str:
        if v is not None and v not in ["alone", "with_family", "with_roommate", "with_partner"]:
            raise ValueError("Invalid living situation")
        return v

    @field_validator("children_status")
    @classmethod
    def validate_children_status(cls, v: str) -> str:
        if v is not None and v not in ["have", "dont_have", "want", "dont_want"]:
            raise ValueError("Invalid children status")
        return v

    @field_validator("smoking")
    @classmethod
    def validate_smoking(cls, v: str) -> str:
        if v is not None and v not in ["never", "occasionally", "regularly"]:
            raise ValueError("Invalid smoking status")
        return v

    @field_validator("drinking")
    @classmethod
    def validate_drinking(cls, v: str) -> str:
        if v is not None and v not in ["never", "socially", "regularly"]:
            raise ValueError("Invalid drinking status")
        return v

    @field_validator("education")
    @classmethod
    def validate_education(cls, v: str) -> str:
        if v is not None and v not in ["high_school", "bachelor", "master", "phd"]:
            raise ValueError("Invalid education level")
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


class LocationTextUpdateRequest(BaseModel):
    """Update user location with text fields."""
    country: Optional[str] = Field(None, max_length=100)
    province: Optional[str] = Field(None, max_length=100)
    city: Optional[str] = Field(None, max_length=100)


class LocationUpdateRequest(BaseModel):
    """Update user location with GPS coordinates."""
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)


# ============ Response Schemas ============

class UserSettingsResponse(BaseModel):
    """Response schema for user settings."""
    hide_last_seen: bool = False
    hide_online_status: bool = False
    push_enabled: bool = True
    like_notifications: bool = True
    match_notifications: bool = True
    message_notifications: bool = True
    language: str = "fa"
    dark_mode: bool = False

    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """Response schema for user profile (excludes sensitive data)."""
    id: UUID
    email: str
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    sexual_orientation: Optional[str] = None
    bio: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    body_type: Optional[str] = None
    relationship_status: Optional[str] = None
    living_situation: Optional[str] = None
    children_status: Optional[str] = None
    smoking: Optional[str] = None
    drinking: Optional[str] = None
    education: Optional[str] = None
    workplace: Optional[str] = None
    religion: Optional[str] = None
    ethnicity: Optional[str] = None
    political_orientation: Optional[str] = None
    languages: Optional[List[str]] = None
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    location_manual: bool = False
    is_premium: bool
    premium_until: Optional[datetime] = None
    is_verified: bool = False
    is_active: bool
    is_profile_complete: bool
    created_at: datetime
    last_seen_at: Optional[datetime] = None
    settings: Optional[UserSettingsResponse] = None
    main_photo_url: Optional[str] = None

    class Config:
        from_attributes = True


class PublicUserResponse(BaseModel):
    """Public profile response for other users (respects privacy settings)."""
    id: UUID
    name: str
    age: int
    gender: str
    sexual_orientation: Optional[str] = None
    bio: Optional[str] = None
    height: Optional[int] = None
    weight: Optional[int] = None
    body_type: Optional[str] = None
    relationship_status: Optional[str] = None
    education: Optional[str] = None
    workplace: Optional[str] = None
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    main_photo_url: Optional[str] = None
    is_premium: bool
    is_verified: bool = False
    last_seen_at: Optional[datetime] = None
    is_online: Optional[bool] = None
    interests: Optional[List[str]] = None

    class Config:
        from_attributes = True

    @classmethod
    def from_user_with_privacy(cls, user, settings, current_user_id: UUID = None):
        """Create public response respecting privacy settings."""
        is_self = current_user_id and user.id == current_user_id
        
        if is_self:
            return cls(
                id=user.id,
                name=user.profile.name,
                age=user.profile.age,
                gender=user.profile.gender,
                sexual_orientation=user.profile.sexual_orientation,
                bio=user.profile.bio,
                height=user.profile.height,
                weight=user.profile.weight,
                body_type=user.profile.body_type,
                relationship_status=user.profile.relationship_status,
                education=user.profile.education,
                workplace=user.profile.workplace,
                country=user.profile.country,
                province=user.profile.province,
                city=user.profile.city,
                main_photo_url=None,
                is_premium=user.profile.is_premium,
                is_verified=user.profile.is_verified,
                last_seen_at=user.last_seen_at,
                is_online=user.last_seen_at and (datetime.now(timezone.utc) - user.last_seen_at).seconds < 300,
                interests=None
            )
        
        if settings.hide_last_seen:
            return cls(
                id=user.id,
                name=user.profile.name,
                age=user.profile.age,
                gender=user.profile.gender,
                sexual_orientation=user.profile.sexual_orientation,
                bio=user.profile.bio,
                height=user.profile.height,
                weight=user.profile.weight,
                body_type=user.profile.body_type,
                relationship_status=user.profile.relationship_status,
                education=user.profile.education,
                workplace=user.profile.workplace,
                country=user.profile.country,
                province=user.profile.province,
                city=user.profile.city,
                main_photo_url=None,
                is_premium=user.profile.is_premium,
                is_verified=user.profile.is_verified,
                last_seen_at=None,
                is_online=None,
                interests=None
            )
        else:
            return cls(
                id=user.id,
                name=user.profile.name,
                age=user.profile.age,
                gender=user.profile.gender,
                sexual_orientation=user.profile.sexual_orientation,
                bio=user.profile.bio,
                height=user.profile.height,
                weight=user.profile.weight,
                body_type=user.profile.body_type,
                relationship_status=user.profile.relationship_status,
                education=user.profile.education,
                workplace=user.profile.workplace,
                country=user.profile.country,
                province=user.profile.province,
                city=user.profile.city,
                main_photo_url=None,
                is_premium=user.profile.is_premium,
                is_verified=user.profile.is_verified,
                last_seen_at=user.last_seen_at,
                is_online=user.last_seen_at and (datetime.now(timezone.utc) - user.last_seen_at).seconds < 300,
                interests=None
            )


class LocationTextUpdateResponse(BaseModel):
    """Response for PATCH /users/me/location-text"""
    country: Optional[str] = None
    province: Optional[str] = None
    city: Optional[str] = None
    location_manual: bool


class DeleteAccountResponse(BaseModel):
    """Response for account deletion."""
    message: str = "Account deleted successfully"


class ChangePasswordRequest(BaseModel):
    """Request schema for password change."""
    current_password: str
    new_password: str = Field(..., min_length=8)


class UserInterestResponse(BaseModel):
    """Response schema for user interests."""
    id: UUID
    name: str
    category: Optional[str] = None
    icon: Optional[str] = None

    class Config:
        from_attributes = True


class UserPromptResponse(BaseModel):
    """Response schema for user prompts."""
    id: UUID
    prompt_id: UUID
    question: str
    answer: str

    class Config:
        from_attributes = True


# ============ Alias for backward compatibility ============
UserResponse = UserProfileResponse