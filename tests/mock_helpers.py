# tests/mock_helpers.py
"""
테스트에 필요한 모킹 헬퍼 함수들
"""

from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy.orm import Session
from app.api.deps import get_db

class MockDBContext:
    """DB 세션을 모킹하는 컨텍스트 매니저"""
    
    def __init__(self):
        self.mock_db = MagicMock(spec=Session)
        self.patcher = patch('app.api.deps.get_db')
        
    def __enter__(self):
        mock_get_db = self.patcher.start()
        mock_get_db.return_value.__next__.return_value = self.mock_db
        return self.mock_db
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.patcher.stop()

@pytest.fixture
def mock_db_fixture():
    """DB 세션을 모킹하는 픽스처"""
    with MockDBContext() as mock_db:
        yield mock_db

def mock_route_db(func):
    """API 라우트의 DB 세션 의존성을 모킹하는 데코레이터"""
    @pytest.fixture
    def mock_db():
        with MockDBContext() as mock_db:
            yield mock_db
    
    patched_func = patch('app.api.deps.get_db')(func)
    patched_func.mock_db = mock_db
    return patched_func