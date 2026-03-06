# tests/conftest.py - 병합 버전

import pytest
import asyncio
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from datetime import datetime

from app.main import app
from app.models.user import User
from app.core.security import create_access_token

# PlanType / Payment 모델이 제거된 경우 폴백
try:
    from app.models.payment import Payment, PaymentStatus
except ImportError:
    Payment = None
    PaymentStatus = None

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# --------------------------
# 이벤트 루프
# --------------------------
@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# --------------------------
# FastAPI 테스트 클라이언트
# --------------------------
@pytest.fixture
def client():
    return TestClient(app)

# --------------------------
# Mock DB 세션
# --------------------------
@pytest.fixture
def db_session():
    return MagicMock(spec=Session)

@pytest.fixture
def db():
    return MagicMock(spec=Session)

# --------------------------
# 테스트 사용자
# --------------------------
@pytest.fixture
def test_user():
    return User(
        id=1,
        email="test@example.com",
        username="testuser",
        full_name="테스트 사용자",
        is_active=True,
        role="user",
        created_at=datetime.utcnow()
    )

# --------------------------
# 인증 관련
# --------------------------
@pytest.fixture
def test_token(test_user):
    return create_access_token(test_user.id)

@pytest.fixture
def auth_headers(test_token):
    return {"Authorization": f"Bearer {test_token}"}

@pytest.fixture
def mock_auth_headers():
    return {"Authorization": "Bearer test_token"}

# --------------------------
# Redis Mock (WebSocket 및 세션용)
# --------------------------
@pytest.fixture(autouse=True)
def mock_redis():
    mock_redis_client = Mock()
    mock_redis_client.from_url.return_value = mock_redis_client
    mock_redis_client.setex.return_value = True
    mock_redis_client.get.return_value = None
    mock_redis_client.exists.return_value = True
    mock_redis_client.expire.return_value = True
    mock_redis_client.delete.return_value = True
    mock_redis_client.lpush.return_value = 1
    mock_redis_client.lrange.return_value = []
    mock_redis_client.llen.return_value = 0
    mock_redis_client.lrem.return_value = 1
    mock_redis_client.sismember.return_value = False
    mock_redis_client.sadd.return_value = 1

    with patch('redis.from_url', return_value=mock_redis_client):
        with patch('app.services.session_manager.redis.from_url', return_value=mock_redis_client):
            yield mock_redis_client

# --------------------------
# LangChain / LangGraph 관련 Mock
# --------------------------
@pytest.fixture
def mock_langchain_llm():
    mock_llm = Mock()
    mock_llm.invoke.return_value = Mock(content="Mock LLM Response")
    with patch('app.services.pdf_agent.nodes.common.llm', mock_llm):
        with patch('app.services.pdf_agent.nodes.qa_system.llm', mock_llm):
            with patch('app.services.pdf_agent.nodes.summary.llm', mock_llm):
                with patch('app.services.pdf_agent.nodes.exam.llm', mock_llm):
                    with patch('app.services.pdf_agent.nodes.scheduler.llm', mock_llm):
                        yield mock_llm

@pytest.fixture
def mock_langraph_agent():
    mock_agent = Mock()
    mock_agent.invoke.return_value = {
        "purpose": "qa",
        "last_assistant_response": "Mock Agent Response",
        "result": "Mock Result"
    }
    with patch('app.services.pdf_agent.graphs.main.intergrate_graph', return_value=mock_agent):
        yield mock_agent

# --------------------------
# 파일 관련 Mock
# --------------------------
@pytest.fixture
def mock_file_operations():
    with patch('os.path.exists', return_value=True):
        with patch('os.listdir', return_value=['test_folder']):
            with patch('os.makedirs'):
                yield

@pytest.fixture
def sample_files():
    return [
        {
            "name": "operating_system.pdf",
            "path": "users/test_user/documents/operating_system.pdf",
            "size": 1024000,
            "type": "pdf",
            "folder": "documents"
        },
        {
            "name": "network_security.pdf",
            "path": "users/test_user/documents/network_security.pdf",
            "size": 2048000,
            "type": "pdf",
            "folder": "documents"
        }
    ]

# --------------------------
# 결제 관련 Mock
# --------------------------
@pytest.fixture
def mock_iamport_client():
    with patch("app.core.iamport_client.IamportClient") as mock:
        mock_client = MagicMock()
        mock_client._get_token.return_value = "mock_token"
        mock_client.get_headers.return_value = {"Authorization": "Bearer mock_token"}
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

@pytest.fixture
def test_payment():
    return Payment(
        id=1,
        imp_uid=None,
        merchant_uid="merchant_test_uid",
        user_id=1,
        amount=15900,
        status=PaymentStatus.ready,
        created_at=datetime.utcnow()
    )

@pytest.fixture
def payment_data():
    return {
        "merchant_uid": "merchant_test_uid",
        "amount": 15900,
        "user_id": 1
    }

@pytest.fixture
def mock_iamport_response():
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

# --------------------------
# 샘플 세션
# --------------------------
@pytest.fixture
def sample_session_data():
    return {
        "session_id": "session:test_user:12345",
        "user_id": "test_user",
        "task_type": "qa",
        "created_at": "2025-05-26T10:00:00",
        "last_activity": "2025-05-26T10:00:00",
        "agent_state": {},
        "waiting_for": None,
        "chat_title": "테스트 채팅",
        "message_history": [],
        "current_request_type": None,
        "selected_files": [],
        "processing_status": "idle"
    }
