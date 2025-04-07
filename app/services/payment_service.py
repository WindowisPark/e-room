# app/services/payment_service.py

from sqlalchemy.orm import Session
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentCreate
from app.core.iamport_client import IamportClient
from datetime import datetime

iamport_client = IamportClient()

def create_payment(db: Session, payment_in: PaymentCreate) -> Payment:
    payment = Payment(
        merchant_uid=payment_in.merchant_uid,
        amount=payment_in.amount,
        user_id=payment_in.user_id,
        status=PaymentStatus.ready
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return payment

def verify_payment(db: Session, imp_uid: str, merchant_uid: str) -> bool:
    # Iamport API로 검증
    payment_data = iamport_client.find_payment_by_imp_uid(imp_uid)
    amount_paid = payment_data["response"]["amount"]

    # DB에 저장된 결제 정보 조회
    db_payment = db.query(Payment).filter(Payment.merchant_uid == merchant_uid).first()

    if db_payment and db_payment.amount == amount_paid:
        db_payment.status = PaymentStatus.paid
        db_payment.imp_uid = imp_uid
        db_payment.paid_at = datetime.utcnow()
        db.commit()
        return True
    else:
        return False

def calculate_subscription_amount(plan_type, duration_months: int) -> float:
    """
    구독 요금제와 기간에 따른 결제 금액 계산
    
    Args:
        plan_type: 요금제 타입 (PlanType)
        duration_months: 구독 기간(월)
        
    Returns:
        결제 금액
    """
    # 월별 요금 (실제 가격으로 조정 필요)
    if plan_type.value == "premium":
        monthly_fee = 15900
    elif plan_type.value == "vip":
        monthly_fee = 29900
    else:  # free
        monthly_fee = 0
    
    # 할인 적용된 총 금액 계산
    total_amount = monthly_fee * duration_months
    
    return total_amount