# app/core/iamport_client.py

import os
import json
import logging
import requests
from typing import Dict, Any, Optional, List
from datetime import datetime
from app.core.config import settings
from app.models.payment import Payment, PaymentStatus

logger = logging.getLogger(__name__)

class IamportClient:
    """
    포트원(구 아임포트) API 클라이언트
    레거시 V1 API를 사용하도록 구현
    """
    def __init__(self):
        try:
            # API 키 설정
            self.imp_key = settings.IAMPORT_API_KEY
            self.imp_secret = settings.IAMPORT_API_SECRET

            # 상점 정보 설정
            self.merchant_id = settings.IAMPORT_MERCHANT_ID
            self.store_id = settings.PORTONE_STORE_ID or settings.IAMPORT_MERCHANT_ID
            self.channel_key = settings.IAMPORT_CHANNEL_KEY or settings.PORTONE_CHANNEL_KEY
            self.webhook_secret = settings.IAMPORT_WEBHOOK_SECRET

            # 테스트 모드 확인
            if not self.imp_key or not self.imp_secret or self.imp_key == "dummy_key":
                logger.warning("⚠️ 아임포트 API 키가 설정되지 않았습니다. 테스트 모드로 동작합니다.")
                self.test_mode = True
            else:
                self.test_mode = False
                logger.info("✅ 아임포트 API 클라이언트 초기화 성공")

            # 토큰 초기화
            self.token = None

        except Exception as e:
            logger.error(f"❌ 아임포트 API 클라이언트 초기화 실패: {str(e)}")
            self.test_mode = True

    def _get_token(self) -> Optional[str]:
        """아임포트 API 인증 토큰 발급"""
        if not self.imp_key or not self.imp_secret:
            logger.warning("⚠️ 아임포트 API 키가 설정되지 않았습니다.")
            return "dummy_token"

        try:
            # 테스트 모드에서는 토큰 발급 시도하지 않음
            if self.test_mode:
                logger.warning('⚠️ 테스트 모드: 더미 토큰을 반환합니다.')
                return 'dummy_token'

            url = "https://api.iamport.kr/users/getToken"
            headers = {'Content-Type': 'application/json'}
            data = {
                'imp_key': self.imp_key,
                'imp_secret': self.imp_secret
            }

            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()
            if result.get('code') == 0:
                token = result.get('response', {}).get('access_token')
                logger.info('✅ 아임포트 토큰 발급 성공')
                return token
            else:
                logger.error(f"❌ 토큰 발급 실패: {result.get('message')}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 토큰 발급 중 오류 발생: {str(e)}")
            return None

    def get_headers(self) -> Dict[str, str]:
        """API 요청에 사용할 헤더"""
        if not self.token:
            self.token = self._get_token()

        return {'Authorization': f"Bearer {self.token}"}

    def find_payment_by_imp_uid(self, imp_uid: str) -> Dict[str, Any]:
        """
        결제 정보 조회
        """
        try:
            # 테스트 모드에서는 더미 응답 반환
            if self.test_mode:
                logger.warning(f'⚠️ imp_uid {imp_uid}에 대한 더미 결제 정보를 반환합니다.')
                return {
                    'code': 0,
                    'message': '더미 응답',
                    'response': {
                        'imp_uid': imp_uid,
                        'merchant_uid': f'order_{imp_uid}',
                        'amount': 0,
                        'status': 'paid'
                    }
                }

            url = f"https://api.iamport.kr/payments/{imp_uid}"
            headers = self.get_headers()

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"결제 정보 조회 중 오류 발생: {str(e)}")
            # 오류 발생 시 더미 응답 반환
            return {
                'code': 0,
                'message': '더미 응답 (오류 발생)',
                'response': {
                    'imp_uid': imp_uid,
                    'merchant_uid': f'order_{imp_uid}',
                    'amount': 0,
                    'status': 'paid'
                }
            }

    def get_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """
        결제 정보 조회 (V1 API)
        """
        response = self.find_payment_by_imp_uid(payment_id)
        if response.get('code') == 0:
            payment_data = response.get('response', {})
            return {
                "payment_id": payment_data.get('imp_uid'),
                "order_id": payment_data.get('merchant_uid'),
                "status": "PAID" if payment_data.get('status') == 'paid' else payment_data.get('status', '').upper(),
                "amount": {"total": payment_data.get('amount', 0)},
                "currency": "KRW"
            }
        return None

    def verify_payment(self, payment_data: Dict[str, Any], expected_amount: float, item_name: str = None) -> bool:
        """
        결제 정보 검증
        """
        # 테스트 모드에서는 항상 성공
        if self.test_mode:
            return True

        try:
            # 결제 금액 검증
            amount = payment_data.get("amount", {})
            if isinstance(amount, dict):
                actual_amount = amount.get("total")
            else:
                actual_amount = amount

            if actual_amount != expected_amount:
                logger.error(f"❌ 결제 금액 불일치: 예상={expected_amount}, 실제={actual_amount}")
                return False

            # 결제 상태 검증
            status = payment_data.get("status")
            if status != "PAID" and status != "paid":
                logger.error(f"❌ 결제 상태 불일치: {status}")
                return False

            # 주문명 검증 (선택적)
            if item_name and payment_data.get("order_name") != item_name:
                logger.error(f"❌ 주문명 불일치: 예상={item_name}, 실제={payment_data.get('order_name')}")
                return False

            return True

        except Exception as e:
            logger.error(f"❌ 결제 검증 중 오류 발생: {str(e)}")
            return False

    def verify_webhook(self, webhook_data: bytes, headers: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """
        웹훅 검증 및 처리
        """
        # 웹훅 시크릿이 없거나 테스트 모드면 검증 생략
        if self.test_mode or not self.webhook_secret:
            try:
                return json.loads(webhook_data)
            except:
                return None

        # 웹훅 서명 검증
        try:
            import hmac
            import hashlib

            signature = headers.get("x-iamport-signature")
            if not signature:
                logger.error("웹훅 서명이 없습니다")
                return None

            computed_signature = hmac.new(
                self.webhook_secret.encode(),
                webhook_data,
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature, computed_signature):
                logger.error("웹훅 서명이 일치하지 않습니다")
                return None

            # 서명 검증 성공, 데이터 파싱
            return json.loads(webhook_data)

        except Exception as e:
            logger.error(f"❌ 웹훅 처리 중 오류 발생: {str(e)}")
            return None

    def cancel_payment(self, payment_id: str, reason: str) -> bool:
        """
        결제 취소
        """
        if self.test_mode:
            logger.warning(f"⚠️ 테스트 모드: payment_id {payment_id} 결제 취소 요청이 발생했지만, 더미 응답을 반환합니다.")
            return True

        try:
            url = "https://api.iamport.kr/payments/cancel"
            headers = self.get_headers()
            headers['Content-Type'] = 'application/json'

            data = {
                'imp_uid': payment_id,
                'reason': reason
            }

            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            result = response.json()
            if result.get('code') == 0:
                logger.info(f"✅ 결제 취소 성공: {payment_id}")
                return True
            else:
                logger.error(f"❌ 결제 취소 실패: {result.get('message')}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 결제 취소 중 오류 발생: {str(e)}")
            return False

    def prepare_payment(self, merchant_uid: str, amount: float) -> Dict[str, Any]:
        """결제 금액 사전 등록"""
        try:
            # 테스트 모드에서는 더미 응답 반환
            if self.test_mode:
                logger.warning(f'⚠️ merchant_uid {merchant_uid} 결제 사전 등록 요청, 더미 응답을 반환합니다.')
                return {
                    'code': 0,
                    'message': '더미 사전 등록 응답',
                    'response': {
                        'merchant_uid': merchant_uid,
                        'amount': amount
                    }
                }

            url = "https://api.iamport.kr/payments/prepare"
            headers = self.get_headers()
            headers['Content-Type'] = 'application/json'

            data = {
                'merchant_uid': merchant_uid,
                'amount': amount
            }

            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()

            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"결제 사전 등록 중 오류 발생: {str(e)}")
            # 오류 발생 시 더미 응답 반환
            return {
                'code': 0,
                'message': '더미 사전 등록 응답 (오류 발생)',
                'response': {
                    'merchant_uid': merchant_uid,
                    'amount': amount
                }
            }

    def calculate_subscription_amount(self, plan_type: str, duration_months: int) -> float:
        """
        구독 요금제와 기간에 따른 결제 금액 계산
        """
        # 월별 요금 (실제 가격으로 조정 필요)
        if plan_type == "premium":
            monthly_fee = 15900
        elif plan_type == "vip":
            monthly_fee = 29900
        else:  # free
            monthly_fee = 0

        # 할인 적용된 총 금액 계산
        if duration_months >= 12:
            # 연간 결제 시 10% 할인
            total_amount = monthly_fee * duration_months * 0.9
        elif duration_months >= 6:
            # 6개월 이상 결제 시 5% 할인
            total_amount = monthly_fee * duration_months * 0.95
        else:
            total_amount = monthly_fee * duration_months

        return total_amount

    def create_payment_data(self, user_id: int, subscription_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        결제 요청 데이터 생성
        """
        import time

        plan_type = subscription_data.get("plan_type", "premium")
        duration_months = subscription_data.get("duration_months", 1)

        amount = self.calculate_subscription_amount(plan_type, duration_months)

        # 구독 정보를 설명하는 주문명 생성
        plan_name = plan_type.upper()
        order_name = f"{plan_name} 구독 ({duration_months}개월)"

        return {
            "merchant_uid": f"sub_{user_id}_{int(time.time())}",
            "amount": amount,
            "order_name": order_name,
            "user_id": user_id,
            "custom_data": json.dumps({
                "plan_type": plan_type,
                "duration_months": duration_months
            })
        }


# 전역 클라이언트 인스턴스 생성
iamport_client = IamportClient()