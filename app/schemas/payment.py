from dataclasses import Field
from app.models.user import PlanType
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import enum

class PaymentStatus(str, enum.Enum):
    ready = "ready"
    paid = "paid"
    cancelled = "cancelled"
    failed = "failed"

class PaymentBase(BaseModel):
    merchant_uid: str
    amount: float

class PaymentCreate(PaymentBase):
    user_id: int

class PaymentOut(PaymentBase):
    id: int
    imp_uid: Optional[str]
    status: PaymentStatus
    paid_at: Optional[datetime]

    class Config:
        orm_mode = True

class SubscriptionPurchase(BaseModel):
    """구독 결제 요청 스키마"""
    plan_type: PlanType
    duration_months: int = 1  # 1-12개월
    payment_method: str
