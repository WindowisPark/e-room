from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any
import time

from app.schemas.payment import PaymentCreate, PaymentOut, SubscriptionPurchase
from app.services.payment_service import create_payment, verify_payment, calculate_subscription_amount
from app.services.subscription_service import upgrade_user_plan
from app.services.notification_service import create_system_notification
from app.models.user import PlanType, User
from app.api import deps
from pydantic import BaseModel, Field

router = APIRouter()

@router.post("/payments", response_model=PaymentOut)
def initiate_payment(
    payment_in: PaymentCreate,
    db: Session = Depends(deps.get_db)
):
    payment = create_payment(db, payment_in)
    return payment

@router.post("/payments/verify")
def confirm_payment(
    imp_uid: str,
    merchant_uid: str,
    db: Session = Depends(deps.get_db)
):
    is_verified = verify_payment(db, imp_uid, merchant_uid)
    if not is_verified:
        raise HTTPException(status_code=400, detail="Payment verification failed.")
    return {"msg": "Payment verified successfully"}

class SubscriptionPurchase(BaseModel):
    """구독 결제 요청 스키마"""
    plan_type: PlanType
    duration_months: int = Field(1, ge=1, le=12)  # 1-12개월
    payment_method: str

# app/api/v1/endpoints/payments.py에 추가

@router.post("/subscribe", response_model=Dict[str, Any])
async def purchase_subscription(
    subscription: SubscriptionPurchase,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """구독 구매 API"""
    # 1. 결제 처리 (기존 payment_service 활용)
    payment_data = PaymentCreate(
        merchant_uid=f"sub_{current_user.id}_{int(time.time())}",
        amount=calculate_subscription_amount(subscription.plan_type, subscription.duration_months),
        user_id=current_user.id
    )
    payment = create_payment(db, payment_data)
    
    # 2. 결제 검증 후 구독 업데이트
    duration_days = subscription.duration_months * 30
    await upgrade_user_plan(db, current_user.id, subscription.plan_type, duration_days)
    
    # 3. 사용자에게 구독 시작 알림
    await create_system_notification(
        db=db,
        user_id=current_user.id,
        message=f"{subscription.plan_type.value.upper()} 요금제 구독이 시작되었습니다.",
        link="/mypage/subscription"
    )
    
    return {
        "success": True,
        "plan": subscription.plan_type,
        "expires_at": current_user.plan_expires_at,
        "max_team_spaces": current_user.max_team_spaces
    }