# app/api/v1/endpoints/phone_verification.py

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel
import logging

from app import crud, schemas
from app.api import deps
from app.models.user import User
from app.services.sms_service import SMSService
sms_service = SMSService()

router = APIRouter()
logger = logging.getLogger(__name__)

# 직접 정의한 전화번호 인증 스키마
class PhoneVerification(BaseModel):
    phone_number: str
    verification_code: str

@router.post("/send-verification")
async def send_verification_code(
    phone_number: str = Body(..., embed=True),
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    현재 로그인한 사용자의 전화번호로 인증 코드 발송
    """
    # 전화번호 형식 검증 (간단한 형식 검증, 필요시 더 정교한 검증 추가)
    if not phone_number or len(phone_number) < 10:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="유효한 전화번호를 입력해주세요"
        )
    
    # 전화번호 저장 (인증 완료 전이므로 인증 상태는 False)
    user_update = {"phone_number": phone_number, "is_phone_verified": False}
    crud.user.update(db, db_obj=current_user, obj_in=user_update)
    
    # 인증 코드 발송
    result = sms_service.send_verification_sms(phone_number)
    
    if not result.get("success"):
        logger.error(f"SMS 발송 실패: {result.get('message')}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=result.get("message", "SMS 발송에 실패했습니다")
        )
    
    return {"message": "인증번호가 발송되었습니다"}

@router.post("/verify")
async def verify_phone_number(
    verification_data: PhoneVerification,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
) -> Dict[str, Any]:
    """
    인증 코드 확인 및 전화번호 인증 처리
    """
    # 사용자의 저장된 전화번호와 요청의 전화번호 일치 여부 확인
    if current_user.phone_number != verification_data.phone_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="저장된 전화번호와 일치하지 않습니다"
        )
    
    # 인증 코드 검증
    is_verified = sms_service.verify_code(
        verification_data.phone_number, 
        verification_data.verification_code
    )
    
    if not is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="인증번호가 일치하지 않거나 만료되었습니다"
        )
    
    # 인증 성공 시 사용자 정보 업데이트
    user_update = {"is_phone_verified": True}
    updated_user = crud.user.update(db, db_obj=current_user, obj_in=user_update)
    
    logger.info(f"전화번호 인증 성공: User ID {current_user.id}, 전화번호: {verification_data.phone_number}")
    
    return {
        "message": "전화번호 인증이 완료되었습니다",
        "is_phone_verified": True
    }

@router.get("/status")
async def get_phone_verification_status(
    current_user: User = Depends(deps.get_current_user)
) -> Dict[str, Any]:
    """
    현재 사용자의 전화번호 인증 상태 조회
    """
    return {
        "phone_number": current_user.phone_number,
        "is_verified": current_user.is_phone_verified
    }

