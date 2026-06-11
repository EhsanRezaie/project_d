from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PlanResponse(BaseModel):
    id: str
    name: str
    days: int
    price_rials: int
    price_usd: float
    discount_percent: int


class SubscriptionPlansResponse(BaseModel):
    plans: List[PlanResponse]


class PurchaseRequest(BaseModel):
    plan_id: str


class PurchaseResponse(BaseModel):
    redirect_url: str
    authority: str


class VerifyResponse(BaseModel):
    success: bool
    message: str
    ref_id: Optional[str] = None


class SubscriptionStatusResponse(BaseModel):
    is_premium: bool
    plan: Optional[str] = None
    started_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    source: Optional[str] = None
    status: Optional[str] = None


class CancelSubscriptionResponse(BaseModel):
    success: bool
    message: str