# app/services/subscription_service.py (신규 파일)

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User, PlanType
from app.crud.crud_team import get_teams_by_owner, get_teams_by_user

async def check_team_creation_permission(db: Session, user_id: int) -> bool:
    """사용자가 새 팀을 생성할 수 있는지 확인"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
        
    # 요금제 활성 여부 확인
    if not user.is_plan_active:
        return False
    
    # 소유한 팀 수 확인
    owned_teams = get_teams_by_owner(db, user_id)
    if len(owned_teams) >= user.max_team_spaces:
        return False
        
    return True

async def upgrade_user_plan(
    db: Session, 
    user_id: int, 
    new_plan: PlanType,
    duration_days: int = 30
) -> bool:
    """사용자 요금제 업그레이드"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
        
    # 새 요금제 적용
    user.plan_type = new_plan
    user.plan_started_at = datetime.now()
    user.plan_expires_at = datetime.now() + timedelta(days=duration_days)
    
    db.commit()
    return True
    
async def handle_plan_expiry(db: Session, user_id: int) -> None:
    """요금제 만료 처리 (배치 작업에서 호출)"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.plan_expires_at:
        return
        
    # 만료 여부 확인
    if user.plan_expires_at > datetime.now():
        return
        
    # 요금제 만료 시 free로 변경
    user.plan_type = PlanType.free
    db.commit()
    
    # TODO: 만료 알림 발송
    # 필요 시 notification_service.py에 연결