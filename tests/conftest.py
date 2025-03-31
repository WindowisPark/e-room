import pytest
import datetime
from datetime import datetime as dt, date
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock, AsyncMock, patch
from urllib.parse import quote_plus

from app.main import app
from app.db.base import Base
from app.models.user import User
from app.api.deps import get_db, get_current_user
from app.core.security import get_password_hash

# PostgreSQL 테스트 DB 연결 정보
password = quote_plus("password123")
TEST_SQLALCHEMY_DATABASE_URL = f"postgresql+psycopg2://postgres:{password}@localhost:5432/test_db"

engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 모든 Redis 관련 모듈 모킹하기
@pytest.fixture(scope="module", autouse=True)
def mock_redis_modules():
    # 일반 Redis 클라이언트 모킹 추가
    with patch("app.core.redis_helper.redis_client") as mock_sync_redis:
        # 동기식 클라이언트 메서드 설정
        mock_sync_redis.sismember.return_value = False
        mock_sync_redis.sadd.return_value = True
        mock_sync_redis.expireat.return_value = True
        
        # 비동기 Redis 클라이언트 설정
        with patch("redis.asyncio.Redis") as mock_redis_class:
            mock_async_client = AsyncMock()
            mock_async_client.publish.return_value = None
            mock_redis_class.return_value = mock_async_client

            with patch("app.services.notification_service.get_redis_client", return_value=mock_async_client), \
                patch("app.core.redis_helper.get_redis_client", return_value=mock_async_client):
                # 둘 다 반환
                yield (mock_sync_redis, mock_async_client)


# DB Fixture
@pytest.fixture(scope="module")
def db():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()

    # ✅ DB에 직접 사용자 추가 시에는 모델(User)을 사용해야 합니다.
    test_user = User(
        id=1,
        email="test@example.com",
        username="testuser",
        full_name="Test User",
        hashed_password=get_password_hash("fakepassword"),
        role="user",
        created_at=dt.now(datetime.timezone.utc)
    )

    session.add(test_user)
    session.commit()
    session.refresh(test_user)

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)

# Redis 클라이언트 Fixture - mock_redis_modules와 연결
@pytest.fixture(scope="module")
def redis_client(mock_redis_modules):
    # 동기식 Redis 클라이언트만 반환 (첫 번째 요소)
    return mock_redis_modules[0]

# 사용자 인증 Mock Fixture
@pytest.fixture(scope="module")
def mock_user():
    return User(
        id=1,
        username="testuser",
        email="testuser@example.com",
        role="user",
        created_at=dt.now(datetime.timezone.utc)
    )

@pytest.fixture(scope="module")
def mock_auth_headers():
    return {"Authorization": "Bearer faketoken"}

# 클라이언트 Fixture
@pytest.fixture(scope="module")
def client(db, mock_user):
    # 의존성 오버라이드
    def override_get_db():
        return db
    
    def override_get_current_user():
        return mock_user
    
    # 의존성 주입
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    with TestClient(app) as test_client:
        yield test_client
    
    # 테스트 후 정리
    app.dependency_overrides.clear()

# 출석 테스트에 필요한 URL 픽스처 추가
@pytest.fixture(scope="module")
def attendance_url():
    return "/api/v1/attendance"