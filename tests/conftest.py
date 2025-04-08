# tests/conftest.py

import pytest
import asyncio
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.models.user import User, PlanType
from app.models.payment import Payment, PaymentStatus
from app.core.security import create_access_token


# 테스트 클라이언트
@pytest.fixture
def client():
    return TestClient(app)


# Mock DB 세션
@pytest.fixture
def db_session():
    """Mock SQLAlchemy 세션"""
    mock_session = MagicMock(spec=Session)
    return mock_session


# 테스트용 DB - 호환성을 위해 db라는 이름으로도 제공
@pytest.fixture
def db():
    """Mock SQLAlchemy 세션 (db_session과 동일)"""
    mock_session = MagicMock(spec=Session)
    return mock_session


# 테스트 사용자
@pytest.fixture
def test_user():
    """테스트 사용자 객체"""
    return User(
        id=1,
        email="test@example.com",
        username="testuser",
        full_name="테스트 사용자",
        plan_type=PlanType.free,
        is_active=True,
        role="user",
        created_at=datetime.utcnow()
    )


# 출석 API URL
@pytest.fixture
def attendance_url():
    """출석 API 엔드포인트"""
    return "/api/v1/attendance"


# 인증 관련 Mock 헤더
@pytest.fixture
def mock_auth_headers():
    """인증 헤더 모킹"""
    return {"Authorization": "Bearer test_token"}


# Redis 클라이언트 모킹
@pytest.fixture
def redis_client():
    """Redis 클라이언트 모킹"""
    mock_redis = MagicMock()
    # 추가적인 Redis 메서드 모킹
    mock_redis.get.return_value = None  # 기본적으로 키가 없음
    mock_redis.setex.return_value = True
    mock_redis.sismember.return_value = False  # 기본적으로 멤버가 없음
    mock_redis.sadd.return_value = 1
    mock_redis.expire.return_value = True
    mock_redis.delete.return_value = 1
    return mock_redis


# 테스트 토큰
@pytest.fixture
def test_token(test_user):
    """테스트 사용자의 JWT 토큰"""
    return create_access_token(test_user.id)


# 인증 헤더
@pytest.fixture
def auth_headers(test_token):
    """인증 헤더"""
    return {"Authorization": f"Bearer {test_token}"}


# Mock IamportClient
@pytest.fixture
def mock_iamport_client():
    """Mock 포트원 클라이언트"""
    with patch("app.core.iamport_client.IamportClient") as mock:
        mock_client = MagicMock()
        
        # _get_token 메소드 모킹
        mock_client._get_token.return_value = "mock_token"
        
        # get_headers 메소드 모킹
        mock_client.get_headers.return_value = {
            "Authorization": "Bearer mock_token"
        }
        
        # find_payment_by_imp_uid 메소드 모킹
        mock_client.find_payment_by_imp_uid.return_value = {
            "code": 0,
            "message": "성공",
            "response": {
                "imp_uid": "imp_test_uid",
                "merchant_uid": "merchant_test_uid",
                "amount": 15900,
                "status": "paid",
                "paid_at": int(datetime.now().timestamp())
            }
        }
        
        # cancel_payment 메소드 모킹
        mock_client.cancel_payment.return_value = {
            "code": 0,
            "message": "취소 성공",
            "response": {
                "imp_uid": "imp_test_uid",
                "merchant_uid": "merchant_test_uid",
                "amount": 15900,
                "status": "cancelled"
            }
        }
        
        mock.return_value = mock_client
        yield mock_client


# 테스트 결제 객체
@pytest.fixture
def test_payment():
    """테스트 결제 객체"""
    return Payment(
        id=1,
        imp_uid=None,
        merchant_uid="merchant_test_uid",
        user_id=1,
        amount=15900,
        status=PaymentStatus.ready,
        created_at=datetime.utcnow()
    )


# 테스트용 결제 데이터
@pytest.fixture
def payment_data():
    """테스트용 결제 데이터"""
    return {
        "merchant_uid": "merchant_test_uid",
        "amount": 15900,
        "user_id": 1
    }


# 테스트용 포트원 응답
@pytest.fixture
def mock_iamport_response():
    """Mock 포트원 API 응답"""
    return {
        "code": 0,
        "message": "성공",
        "response": {
            "imp_uid": "imp_test_uid",
            "merchant_uid": "merchant_test_uid",
            "amount": 15900,
            "status": "paid",
            "paid_at": 1617961617
        }
    }


# asyncio 이벤트 루프 (비동기 테스트용)
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()