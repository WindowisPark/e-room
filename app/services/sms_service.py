# app/services/sms_service.py

import logging
import random
import string
from typing import Dict, Any, Optional

from app.core.config import settings
from app.core.redis_helper import redis_client

logger = logging.getLogger(__name__)

# 인증번호 만료 시간 (초)
VERIFICATION_CODE_EXPIRY = 300  # 5분

class SMSService:
    """
    간소화된 SMS 서비스 (실제 SMS 발송 없이 로그만 출력)
    """
    
    @staticmethod
    def generate_verification_code(length: int = 6) -> str:
        """
        랜덤 인증번호 생성
        """
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def store_verification_code(phone_number: str, code: str) -> None:
        """
        Redis에 인증번호 저장
        """
        redis_key = f"sms:verification:{phone_number}"
        redis_client.setex(redis_key, VERIFICATION_CODE_EXPIRY, code)
        
    @staticmethod
    def verify_code(phone_number: str, code: str) -> bool:
        """
        인증번호 검증
        """
        redis_key = f"sms:verification:{phone_number}"
        stored_code = redis_client.get(redis_key)
        
        if not stored_code:
            return False
            
        stored_code_str = stored_code.decode('utf-8')
        if stored_code_str == code:
            # 인증 성공 시 코드 삭제
            redis_client.delete(redis_key)
            return True
            
        return False
    
    @classmethod
    def send_verification_sms(cls, phone_number: str) -> Dict[str, Any]:
        """
        인증번호 SMS 발송 (개발 모드 - 실제 발송 안함)
        """
        # 인증 코드 생성 및 저장
        code = cls.generate_verification_code()
        cls.store_verification_code(phone_number, code)
        
        # 로그에 출력
        logger.info(f"[개발모드] 전화번호 {phone_number}에 인증번호 {code} 발송 (5분간 유효)")
        return {
            "success": True, 
            "code": code, 
            "message": "개발 모드에서는 실제 SMS가 발송되지 않습니다."
        }

sms_service = SMSService()