"""Face Verification schemas."""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ChallengeResponse(BaseModel):
    """Response when generating a liveness challenge."""
    challenge_type: str
    instructions: str
    challenge_id: str
    expires_in_seconds: int = 600


class VerifyRequest(BaseModel):
    """Request to submit verification video."""
    challenge_id: str
    challenge_type: str


class VerifyResponse(BaseModel):
    """Response after verification attempt."""
    verified: bool
    message: str
    similarity_score: Optional[float] = None


class VerificationStatusResponse(BaseModel):
    """Response for verification status check."""
    is_verified: bool
    verified_at: Optional[datetime] = None
    eligible_to_verify: bool
    cooldown_remaining_seconds: Optional[int] = None
