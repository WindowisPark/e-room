# tests/test_subscription_simple.py
import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from app.models.user import User, PlanType
from app.services.subscription_service import check_team_creation_permission

# 구독 정보가 있는 사용자 준비
@pytest.mark.asyncio
async def test_check_permission_direct(db):
    """직접 함수 호출 테스트"""
    # 사용자 준비
    user = db.query(User).filter(User.id == 1).first()
    
    # Free 플랜
    user.plan_type = PlanType.free
    db.commit()
    
    # 직접 함수 호출 - Free는 false 예상
    result = await check_team_creation_permission(db, user.id)
    assert result is False
    
    # Premium으로 업그레이드 (활성 상태)
    user.plan_type = PlanType.premium
    user.plan_started_at = datetime.now()
    user.plan_expires_at = datetime.now() + timedelta(days=30)
    db.commit()
    
    # 다시 함수 호출 - Premium + 활성 + 팀없음 = True 예상
    result = await check_team_creation_permission(db, user.id)
    assert result is True