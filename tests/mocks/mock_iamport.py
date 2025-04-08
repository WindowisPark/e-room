# tests/mocks/mock_iamport.py

import json
from datetime import datetime
from unittest.mock import MagicMock
from typing import Dict, Any

class MockIamportClient:
    """
    포트원 클라이언트 모킹 클래스
    테스트에서 실제 API 호출 없이 결제 테스트를 할 수 있게 함
    """
    
    def __init__(self, success=True, paid_amount=15900):
        self.success = success
        self.paid_amount = paid_amount
        self.token = "mock_access_token_for_testing"
        
        # 테스트용 결제 데이터
        self.payments = {}
    
    def _get_token(self) -> str:
        """토큰 발급 모킹"""
        return self.token

    def get_headers(self) -> Dict[str, str]:
        """API 요청 헤더 모킹"""
        return {"Authorization": f"Bearer {self.token}"}

    def find_payment_by_imp_uid(self, imp_uid: str) -> Dict[str, Any]:
        """결제 정보 조회 모킹"""
        # 저장된 결제 정보가 있으면 반환
        if imp_uid in self.payments:
            payment = self.payments[imp_uid]
            return {
                "code": 0,
                "message": "성공",
                "response": payment
            }
        
        # 기본 응답 생성
        status = "paid" if self.success else "failed"
        payment = {
            "imp_uid": imp_uid,
            "merchant_uid": f"merchant_{imp_uid[4:]}",  # imp_xxx에서 merchant_xxx 형태로 변환
            "amount": self.paid_amount,
            "status": status,
            "paid_at": int(datetime.now().timestamp()) if self.success else None
        }
        
        # 테스트용으로 저장
        self.payments[imp_uid] = payment
        
        return {
            "code": 0 if self.success else 1,
            "message": "성공" if self.success else "결제 실패",
            "response": payment
        }

    def cancel_payment(self, imp_uid: str, reason: str) -> Dict[str, Any]:
        """결제 취소 모킹"""
        if imp_uid not in self.payments:
            return {
                "code": 1,
                "message": "존재하지 않는 결제입니다",
                "response": None
            }
        
        payment = self.payments[imp_uid]
        
        # 이미 취소된 결제
        if payment["status"] == "cancelled":
            return {
                "code": 1,
                "message": "이미 취소된 결제입니다",
                "response": payment
            }
        
        # 결제 취소 처리
        payment["status"] = "cancelled"
        self.payments[imp_uid] = payment
        
        return {
            "code": 0,
            "message": "취소 성공",
            "response": payment
        }

    def create_payment(self, merchant_uid: str, amount: float, name: str, buyer_email: str) -> Dict[str, Any]:
        """결제 생성 모킹 (포트원 API에는 없지만 테스트용)"""
        imp_uid = f"imp_test_{merchant_uid[-8:]}"
        
        payment = {
            "imp_uid": imp_uid,
            "merchant_uid": merchant_uid,
            "amount": amount,
            "name": name,
            "buyer_email": buyer_email,
            "status": "ready",
            "created_at": int(datetime.now().timestamp())
        }
        
        self.payments[imp_uid] = payment
        
        return {
            "code": 0,
            "message": "결제 생성 성공",
            "response": payment
        }

    def complete_payment(self, imp_uid: str) -> Dict[str, Any]:
        """결제 완료 처리 모킹 (테스트용)"""
        if imp_uid not in self.payments:
            return {
                "code": 1, 
                "message": "존재하지 않는 결제입니다",
                "response": None
            }
        
        payment = self.payments[imp_uid]
        payment["status"] = "paid"
        payment["paid_at"] = int(datetime.now().timestamp())
        
        self.payments[imp_uid] = payment
        
        return {
            "code": 0,
            "message": "결제 완료",
            "response": payment
        }


# 포트원 웹훅 요청 모킹 함수
def generate_mock_webhook_data(imp_uid: str, merchant_uid: str, status: str, amount: float) -> Dict[str, Any]:
    """테스트용 웹훅 데이터 생성"""
    return {
        "imp_uid": imp_uid,
        "merchant_uid": merchant_uid,
        "status": status,
        "amount": amount,
        "paid_at": int(datetime.now().timestamp()),
        "receipt_url": f"https://mockurl.com/receipt/{imp_uid}"
    }


# 포트원 웹훅 서명 모킹 함수
def generate_mock_webhook_signature(data: Dict[str, Any], secret: str) -> str:
    """테스트용 웹훅 서명 생성"""
    # 실제로는 HMAC-SHA256 서명이 필요하지만 테스트에서는 간단히 처리
    return "mock_signature_for_testing"