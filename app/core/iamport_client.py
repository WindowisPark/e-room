# 더미 구현체 - 실제 requests 라이브러리 사용 없이 작동
import logging
from typing import Dict
from app.core.config import settings

logger = logging.getLogger(__name__)

class IamportClient:
    def __init__(self):
        logger.warning('⚠️ 포트원 결제 기능은 현재 비활성화되어 있습니다. (TODO: requests 라이브러리 문제 해결 필요)')
        self.api_url = 'https://api.iamport.kr/'
        try:
            self.imp_key = settings.IAMPORT_API_KEY
            self.imp_secret = settings.IAMPORT_API_SECRET
        except AttributeError:
            self.imp_key = 'dummy_key'
            self.imp_secret = 'dummy_secret'
        self.token = 'dummy_token'

    def _get_token(self) -> str:
        logger.warning('⚠️ 더미 토큰을 반환합니다.')
        return self.token

    def get_headers(self) -> Dict[str, str]:
        return {'Authorization': self._get_token()}

    def find_payment_by_imp_uid(self, imp_uid: str) -> Dict:
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

    def cancel_payment(self, imp_uid: str, reason: str) -> Dict:
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
