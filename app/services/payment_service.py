# app/services/payment_service.py

from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, Dict, Any
import logging

from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentCreate
from app.core.iamport_client import iamport_client

logger = logging.getLogger(__name__)

def create_payment(db: Session, payment_in: PaymentCreate) -> Payment:
    """
    결제 정보 생성 (결제 요청 시 호출)
    
    Args:
        db: 데이터베이스 세션
        payment_in: 결제 생성 스키마
        
    Returns:
        생성된 Payment 객체
    """
    payment = Payment(
        merchant_uid=payment_in.merchant_uid,
        amount=payment_in.amount,
        user_id=payment_in.user_id,
        status=PaymentStatus.ready
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)
    logger.info(f"결제 정보 생성 완료: {payment_in.merchant_uid}")
    return payment

def update_payment_status(
    db: Session, 
    merchant_uid: str, 
    status: PaymentStatus,
    imp_uid: Optional[str] = None
) -> Optional[Payment]:
    """
    결제 상태 업데이트
    
    Args:
        db: 데이터베이스 세션
        merchant_uid: 상점 주문번호
        status: 변경할 결제 상태
        imp_uid: 포트원 결제 고유번호 (있는 경우)
        
    Returns:
        업데이트된 Payment 객체 또는 None
    """
    payment = db.query(Payment).filter(Payment.merchant_uid == merchant_uid).first()
    if not payment:
        logger.error(f"결제 정보를 찾을 수 없음: {merchant_uid}")
        return None
    
    payment.status = status
    if imp_uid:
        payment.imp_uid = imp_uid
    
    if status == PaymentStatus.paid:
        payment.paid_at = datetime.utcnow()
    
    db.commit()
    db.refresh(payment)
    logger.info(f"결제 상태 업데이트: {merchant_uid}, 상태: {status}")
    return payment

def verify_payment(db: Session, imp_uid: str, merchant_uid: str) -> bool:
    """
    포트원 API를 통해 결제 정보 검증
    
    Args:
        db: 데이터베이스 세션
        imp_uid: 포트원 결제 고유번호
        merchant_uid: 상점 주문번호
        
    Returns:
        검증 성공 여부
    """
    try:
        # 포트원 API로 결제 정보 조회
        payment_data = iamport_client.find_payment_by_imp_uid(imp_uid)
        if not payment_data or payment_data.get('code') != 0:
            logger.error(f"포트원 API에서 결제 정보를 찾을 수 없음: {imp_uid}")
            return False
        
        # DB에 저장된 결제 정보 조회
        db_payment = db.query(Payment).filter(Payment.merchant_uid == merchant_uid).first()
        if not db_payment:
            logger.error(f"DB에서 결제 정보를 찾을 수 없음: {merchant_uid}")
            return False
        
        # 결제 응답 데이터 추출
        response_data = payment_data.get('response', {})
        if not response_data:
            logger.error(f"결제 응답 데이터가 없음: {payment_data}")
            return False
        
        # 결제 금액 검증
        if response_data.get('amount') != db_payment.amount:
            logger.error(f"결제 금액 불일치: DB={db_payment.amount}, PG={response_data.get('amount')}")
            return False
        
        # 결제 상태 검증
        if response_data.get('status') != 'paid':
            logger.error(f"결제 상태 불일치: {response_data.get('status')}")
            return False
        
        # 결제 정보 업데이트
        db_payment.status = PaymentStatus.paid
        db_payment.imp_uid = imp_uid
        db_payment.paid_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"결제 검증 성공: {merchant_uid}")
        return True
        
    except Exception as e:
        logger.error(f"결제 검증 중 오류 발생: {str(e)}")
        return False

def calculate_subscription_amount(plan_type: str, duration_months: int) -> float:
    """
    구독 요금제와 기간에 따른 결제 금액 계산
    
    Args:
        plan_type: 요금제 타입 (premium, vip 등)
        duration_months: 구독 기간(월)
        
    Returns:
        결제 금액
    """
    return iamport_client.calculate_subscription_amount(plan_type, duration_months)

def get_user_payments(db: Session, user_id: int, limit: int = 10) -> list[Payment]:
    """
    사용자의 결제 내역 조회
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        limit: 조회할 최대 결제 수
        
    Returns:
        Payment 객체 목록
    """
    return db.query(Payment)\
        .filter(Payment.user_id == user_id)\
        .order_by(Payment.created_at.desc())\
        .limit(limit)\
        .all()

def get_payment_by_id(db: Session, payment_id: str, user_id: Optional[int] = None) -> Optional[Payment]:
    """
    결제 ID로 결제 정보 조회
    
    Args:
        db: 데이터베이스 세션
        payment_id: 결제 ID (merchant_uid 또는 imp_uid)
        user_id: 사용자 ID (검증용, 없으면 검증 생략)
        
    Returns:
        Payment 객체 또는 None
    """
    query = db.query(Payment)
    
    # merchant_uid 또는 imp_uid로 검색
    query = query.filter(
        (Payment.merchant_uid == payment_id) | 
        (Payment.imp_uid == payment_id)
    )
    
    # 사용자 ID가 지정된 경우 해당 사용자의 결제만 조회
    if user_id:
        query = query.filter(Payment.user_id == user_id)
    
    return query.first()