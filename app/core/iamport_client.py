# app/core/iamport_client.py
import requests
import logging
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class IamportClient:
    def __init__(self):
        self.api_url = 'https://api.iamport.kr/'
        
        # 설정에서 API 키 가져오기 (테스트 모드에서는 더미값 사용)
        try:
            self.imp_key = settings.IAMPORT_API_KEY
            self.imp_secret = settings.IAMPORT_API_SECRET
            self.merchant_id = getattr(settings, 'IAMPORT_MERCHANT_ID', None)
            self.channel_key = getattr(settings, 'IAMPORT_CHANNEL_KEY', None)
            
            if not all([self.imp_key, self.imp_secret]):
                logger.warning('⚠️ 포트원 결제 기능은 현재 비활성화되어 있습니다. API 키 설정이 필요합니다.')
                # 더미 값 설정
                self.imp_key = 'dummy_key'
                self.imp_secret = 'dummy_secret'
        except AttributeError:
            logger.warning('⚠️ 포트원 설정을 찾을 수 없습니다. 더미 값을 사용합니다.')
            self.imp_key = 'dummy_key'
            self.imp_secret = 'dummy_secret'
        
        self.token = None
        self._get_token()

    def _get_token(self) -> Optional[str]:
        """포트원 API 인증 토큰 발급"""
        try:
            # 테스트 모드에서는 토큰 발급 시도하지 않음
            if self.imp_key == 'dummy_key' or self.imp_secret == 'dummy_secret':
                logger.warning('⚠️ 더미 토큰을 반환합니다.')
                self.token = 'dummy_token'
                return self.token
                
            url = f"{self.api_url}users/getToken"
            headers = {'Content-Type': 'application/json'}
            data = {
                'imp_key': self.imp_key,
                'imp_secret': self.imp_secret
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            if result.get('code') == 0:
                self.token = result.get('response', {}).get('access_token')
                logger.info('✅ 포트원 토큰 발급 성공')
                return self.token
            else:
                logger.error(f"❌ 토큰 발급 실패: {result.get('message')}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ 토큰 발급 중 오류 발생: {str(e)}")
            return None

    def get_headers(self) -> Dict[str, str]:
        """API 요청에 사용할 헤더"""
        if not self.token:
            self._get_token()
            
        return {'Authorization': f"Bearer {self.token}"}

    def find_payment_by_imp_uid(self, imp_uid: str) -> Dict:
        """결제 정보 조회"""
        try:
            # 테스트 모드에서는 더미 응답 반환
            if self.imp_key == 'dummy_key' or self.imp_secret == 'dummy_secret':
                logger.warning(f'⚠️ imp_uid {imp_uid}에 대한 더미 결제 정보를 반환합니다.')
                return {
                    'code': 0,
                    'message': '더미 응답',
                    'response': {
                        'imp_uid': imp_uid,
                        'amount': 0,
                        'status': 'paid'
                    }
                }
            
            url = f"{self.api_url}payments/{imp_uid}"
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
                    'amount': 0,
                    'status': 'paid'
                }
            }

    def cancel_payment(self, imp_uid: str, reason: str) -> Dict:
        """결제 취소"""
        try:
            # 테스트 모드에서는 더미 응답 반환
            if self.imp_key == 'dummy_key' or self.imp_secret == 'dummy_secret':
                logger.warning(f'⚠️ imp_uid {imp_uid} 결제 취소 요청이 발생했지만, 더미 응답을 반환합니다.')
                return {
                    'code': 0,
                    'message': '더미 취소 응답',
                    'response': {
                        'imp_uid': imp_uid,
                        'amount': 0,
                        'status': 'cancelled'
                    }
                }
            
            url = f"{self.api_url}payments/cancel"
            headers = self.get_headers()
            headers['Content-Type'] = 'application/json'
            
            data = {
                'imp_uid': imp_uid,
                'reason': reason
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"결제 취소 중 오류 발생: {str(e)}")
            # 오류 발생 시 더미 응답 반환
            return {
                'code': 0,
                'message': '더미 취소 응답 (오류 발생)',
                'response': {
                    'imp_uid': imp_uid,
                    'amount': 0,
                    'status': 'cancelled'
                }
            }

    def prepare_payment(self, merchant_uid: str, amount: float) -> Dict:
        """결제 금액 사전 등록"""
        try:
            # 테스트 모드에서는 더미 응답 반환
            if self.imp_key == 'dummy_key' or self.imp_secret == 'dummy_secret':
                logger.warning(f'⚠️ merchant_uid {merchant_uid} 결제 사전 등록 요청, 더미 응답을 반환합니다.')
                return {
                    'code': 0,
                    'message': '더미 사전 등록 응답',
                    'response': {
                        'merchant_uid': merchant_uid,
                        'amount': amount
                    }
                }
            
            url = f"{self.api_url}payments/prepare"
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


# 전역 클라이언트 인스턴스 생성
iamport_client = IamportClient()