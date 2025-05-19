# app/api/v1/endpoints/payments.py

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Body, Header
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional
import json
import logging

from app.api import deps
from app.db.session import get_db
from app.models.user import User, PlanType
from app.models.payment import Payment, PaymentStatus
from app.schemas.payment import PaymentCreate, PaymentOut, SubscriptionPurchase
from app.core.iamport_client import iamport_client
from app.services.payment_service import create_payment, update_payment_status, get_user_payments, get_payment_by_id
from app.services.subscription_service import upgrade_user_plan
from app.services.notification_service import create_system_notification

logger = logging.getLogger(__name__)
router = APIRouter()

# 결제 요청 초기화
@router.post("/subscribe", response_model=Dict[str, Any])
async def purchase_subscription(
    subscription: SubscriptionPurchase,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    구독 결제 요청 초기화 API

    - 포트원 결제 요청에 필요한 정보 생성
    - 결제 정보 DB에 저장 (대기 상태)
    - 결제창 호출에 필요한 정보 반환
    """
    try:
        # 결제 데이터 생성
        payment_data = iamport_client.create_payment_data(
            user_id=current_user.id,
            subscription_data={
                "plan_type": subscription.plan_type.value,
                "duration_months": subscription.duration_months
            }
        )

        # DB에 결제 정보 저장 (READY 상태)
        payment = create_payment(db, PaymentCreate(
            merchant_uid=payment_data["merchant_uid"],
            amount=payment_data["amount"],
            user_id=current_user.id
        ))

        # 클라이언트에 필요한 정보 반환
        return {
            "success": True,
            "payment_info": {
                "merchant_uid": payment_data["merchant_uid"],
                "amount": payment_data["amount"],
                "order_name": payment_data["order_name"],
                "custom_data": payment_data.get("custom_data"),
                "buyer_name": current_user.full_name,
                "buyer_email": current_user.email,
                "buyer_tel": current_user.phone_number,
                # 포트원 SDK 연동에 필요한 정보
                "store_id": iamport_client.store_id,
                "channel_key": iamport_client.channel_key,
            }
        }
    except Exception as e:
        logger.error(f"결제 요청 초기화 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"결제 요청 초기화 실패: {str(e)}")

# 결제 완료 처리
@router.post("/complete")
async def complete_payment(
    payment_id: str = Body(..., embed=True, alias="paymentId"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    결제 완료 처리 API (클라이언트에서 결제 완료 후 호출)

    - 포트원 API로 결제 정보 조회
    - 결제 정보 검증
    - 결제 상태 업데이트
    - 구독 정보 업데이트
    """
    try:
        # 포트원 API로 결제 정보 조회 (V2 API)
        payment_data = iamport_client.get_payment(payment_id)

        # V2 API 실패 시 V1 API 시도
        if not payment_data:
            v1_response = iamport_client.find_payment_by_imp_uid(payment_id)
            if v1_response and v1_response.get('code') == 0:
                payment_data = {
                    "payment_id": payment_id,
                    "order_id": v1_response.get('response', {}).get('merchant_uid'),
                    "status": "PAID" if v1_response.get('response', {}).get('status') == 'paid' else v1_response.get('response', {}).get('status', '').upper(),
                    "amount": {"total": v1_response.get('response', {}).get('amount', 0)}
                }
            else:
                logger.error(f"결제 정보 조회 실패: {payment_id}")
                raise HTTPException(status_code=400, detail="결제 정보를 찾을 수 없습니다.")

        # merchant_uid 추출
        merchant_uid = payment_data.get("order_id")
        if not merchant_uid:
            logger.error(f"merchant_uid가 없습니다: {payment_data}")
            raise HTTPException(status_code=400, detail="유효하지 않은 결제 정보입니다.")

        # DB에서 결제 정보 조회
        db_payment = db.query(Payment).filter(Payment.merchant_uid == merchant_uid).first()
        if not db_payment:
            logger.error(f"DB에서 결제 정보를 찾을 수 없습니다: {merchant_uid}")
            raise HTTPException(status_code=400, detail="결제 정보를 찾을 수 없습니다.")

        # 이미 처리된 결제인지 확인
        if db_payment.status == PaymentStatus.paid:
            logger.info(f"이미 처리된 결제입니다: {merchant_uid}")
            return {"success": True, "message": "이미 처리된 결제입니다."}

        # 결제 정보 검증
        amount = payment_data.get("amount", {})
        if isinstance(amount, dict):
            actual_amount = amount.get("total")
        else:
            actual_amount = amount

        if actual_amount != db_payment.amount:
            logger.error(f"결제 금액 불일치: DB={db_payment.amount}, 결제={actual_amount}")
            raise HTTPException(status_code=400, detail="결제 정보 검증에 실패했습니다.")

        # 결제 상태 업데이트
        update_payment_status(
            db,
            merchant_uid=merchant_uid,
            status=PaymentStatus.paid,
            imp_uid=payment_id
        )

        # 구독 정보 처리
        custom_data = payment_data.get("custom_data", {})
        if isinstance(custom_data, str):
            try:
                custom_data = json.loads(custom_data)
            except:
                custom_data = {}

        plan_type = custom_data.get("plan_type", "premium")
        duration_months = int(custom_data.get("duration_months", 1))

        # 구독 업그레이드
        await upgrade_user_plan(
            db,
            user_id=current_user.id,
            new_plan=PlanType(plan_type),
            duration_days=duration_months * 30
        )

        # 알림 생성
        await create_system_notification(
            db=db,
            user_id=current_user.id,
            message=f"{plan_type.upper()} 요금제 구독이 시작되었습니다!",
            link="/mypage/subscription"
        )

        return {
            "success": True,
            "plan": plan_type,
            "duration_months": duration_months,
            "expires_at": current_user.plan_expires_at,
            "max_team_spaces": current_user.max_team_spaces
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"결제 완료 처리 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"결제 처리 중 오류가 발생했습니다: {str(e)}")

# 결제 취소
@router.post("/cancel/{payment_id}")
async def cancel_payment(
    payment_id: str,
    reason: str = Body(..., embed=True),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_admin_user)  # get_current_admin → get_admin_user로 변경
):
    """
    결제 취소 API (관리자 전용)

    - 포트원 API로 결제 취소 요청
    - DB 결제 상태 업데이트
    """
    try:
        # 결제 취소 요청
        success = iamport_client.cancel_payment(payment_id, reason)
        if not success:
            raise HTTPException(status_code=400, detail="결제 취소에 실패했습니다.")

        # DB 상태 업데이트
        db_payment = db.query(Payment).filter(Payment.imp_uid == payment_id).first()
        if db_payment:
            db_payment.status = PaymentStatus.cancelled
            db.commit()

        return {"success": True, "message": "결제가 취소되었습니다."}

    except Exception as e:
        logger.error(f"결제 취소 실패: {str(e)}")
        raise HTTPException(status_code=500, detail=f"결제 취소 중 오류가 발생했습니다: {str(e)}")

# 웹훅 처리
@router.post("/webhook")
async def payment_webhook(
    request: Request,
    db: Session = Depends(deps.get_db)
):
    """
    포트원 웹훅 수신 처리

    - 웹훅 서명 검증
    - 결제 상태에 따른 처리
    """
    try:
        # 요청 바디와 헤더 가져오기
        body = await request.body()
        headers = dict(request.headers)

        # 웹훅 검증
        webhook_data = iamport_client.verify_webhook(body, headers)
        if not webhook_data:
            logger.error("웹훅 검증 실패")
            return {"message": "Invalid webhook signature"}, 400

        # 결제 ID 확인
        payment_id = webhook_data.get("payment_id") or webhook_data.get("imp_uid")
        if not payment_id:
            logger.error("웹훅에 payment_id가 없습니다")
            return {"message": "No payment_id in webhook data"}, 400

        # 결제 정보 조회
        payment_data = iamport_client.get_payment(payment_id) or iamport_client.find_payment_by_imp_uid(payment_id)
        if not payment_data:
            logger.error(f"결제 정보 조회 실패: {payment_id}")
            return {"message": "Payment not found"}, 200  # 재시도 방지를 위해 200 반환

        # merchant_uid로 DB 결제 정보 조회
        merchant_uid = None
        if isinstance(payment_data, dict):
            merchant_uid = payment_data.get("order_id") or payment_data.get("merchant_uid")
        elif payment_data.get('response'):
            merchant_uid = payment_data.get('response', {}).get('merchant_uid')

        if not merchant_uid:
            logger.error(f"merchant_uid가 없습니다: {payment_data}")
            return {"message": "No merchant_uid in payment data"}, 200

        db_payment = db.query(Payment).filter(Payment.merchant_uid == merchant_uid).first()
        if not db_payment:
            logger.error(f"DB에서 결제 정보를 찾을 수 없습니다: {merchant_uid}")
            return {"message": "Payment not found in DB"}, 200

        # 이벤트 타입에 따른 처리
        event_type = webhook_data.get("type") or webhook_data.get("status")

        # 포트원 V1 웹훅 처리
        if webhook_data.get('imp_uid'):
            status = webhook_data.get('status')
            if status == 'paid' and db_payment.status != PaymentStatus.paid:
                db_payment.status = PaymentStatus.paid
                db_payment.imp_uid = webhook_data.get('imp_uid')
                db_payment.paid_at = datetime.utcnow()
                db.commit()
                logger.info(f"웹훅으로 결제 완료 처리 (V1): {merchant_uid}")
            elif status == 'cancelled' and db_payment.status != PaymentStatus.cancelled:
                db_payment.status = PaymentStatus.cancelled
                db.commit()
                logger.info(f"웹훅으로 결제 취소 처리 (V1): {merchant_uid}")
            elif status == 'failed' and db_payment.status != PaymentStatus.failed:
                db_payment.status = PaymentStatus.failed
                db.commit()
                logger.info(f"웹훅으로 결제 실패 처리 (V1): {merchant_uid}")

        # 포트원 V2 웹훅 처리
        elif event_type == "PAYMENT_STATUS_CHANGED":
            status = webhook_data.get("status")
            if status == "PAID" and db_payment.status != PaymentStatus.paid:
                db_payment.status = PaymentStatus.paid
                db_payment.imp_uid = payment_id
                db_payment.paid_at = datetime.utcnow()
                db.commit()
                logger.info(f"웹훅으로 결제 완료 처리 (V2): {merchant_uid}")
            elif status == "CANCELLED" and db_payment.status != PaymentStatus.cancelled:
                db_payment.status = PaymentStatus.cancelled
                db.commit()
                logger.info(f"웹훅으로 결제 취소 처리 (V2): {merchant_uid}")
            elif status == "FAILED" and db_payment.status != PaymentStatus.failed:
                db_payment.status = PaymentStatus.failed
                db.commit()
                logger.info(f"웹훅으로 결제 실패 처리 (V2): {merchant_uid}")

        return {"message": "Webhook processed successfully"}, 200

    except Exception as e:
        logger.error(f"웹훅 처리 실패: {str(e)}")
        return {"message": "Error processing webhook"}, 500

# 결제 내역 조회
@router.get("/history", response_model=List[PaymentOut])
async def get_payment_history(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    사용자의 결제 내역 조회
    """
    try:
        payments = get_user_payments(db, current_user.id)
        return payments
    except Exception as e:
        logger.error(f"결제 내역 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="결제 내역 조회 중 오류가 발생했습니다.")

# 결제 정보 조회
@router.get("/{payment_id}", response_model=PaymentOut)
async def get_payment(
    payment_id: str,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    특정 결제 정보 조회
    """
    try:
        payment = get_payment_by_id(db, payment_id, current_user.id)

        if not payment:
            raise HTTPException(status_code=404, detail="결제 정보를 찾을 수 없습니다.")

        return payment
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"결제 정보 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="결제 정보 조회 중 오류가 발생했습니다.")