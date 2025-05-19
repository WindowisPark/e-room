# app/services/team_activity_service.py

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import joinedload, Session
from datetime import datetime, timedelta

from app.models.team_activity import TeamActivity
from app.schemas.collaboration import TeamActivityLogCreate

async def log_team_activity(
    db: Session,
    team_id: int,
    user_id: int,
    action: str,
    resource_type: str,
    resource_id: Optional[int] = None,
    details: Optional[Dict[str, Any]] = None
) -> TeamActivity:
    """
    팀 활동 로그 기록

    Args:
        db: 데이터베이스 세션
        team_id: 팀 ID
        user_id: 활동 수행한 사용자 ID
        action: 수행된 액션 (create, update, delete 등)
        resource_type: 리소스 유형 (pdf, annotation, comment 등)
        resource_id: 관련 리소스 ID (있는 경우)
        details: 활동 상세 정보 (JSON으로 저장)

    Returns:
        생성된 TeamActivity 객체
    """
    activity = TeamActivity(
        team_id=team_id,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        created_at=datetime.utcnow()
    )

    db.add(activity)
    db.commit()
    db.refresh(activity)

    return activity

async def get_team_activities(
    db: Session,
    team_id: int,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    page: int = 1,
    limit: int = 50
) -> List[TeamActivity]:
    """
    팀 활동 로그 조회 (필터링 및 페이지네이션 지원)

    Args:
        db: 데이터베이스 세션
        team_id: 팀 ID
        start_date: 시작 날짜 필터
        end_date: 종료 날짜 필터
        user_id: 사용자 ID 필터
        resource_type: 리소스 유형 필터
        action: 액션 필터
        page: 페이지 (1부터 시작)
        limit: 페이지당 결과 수

    Returns:
        TeamActivity 객체 목록
    """


    query = db.query(TeamActivity).options(joinedload(TeamActivity.user))  # ✅ 먼저 선언

    query = query.filter(TeamActivity.team_id == team_id)

    if start_date:
        query = query.filter(TeamActivity.created_at >= start_date)



    if end_date:
        query = query.filter(TeamActivity.created_at <= end_date)

    if user_id:
        query = query.filter(TeamActivity.user_id == user_id)

    if resource_type:
        query = query.filter(TeamActivity.resource_type == resource_type)

    if action:
        query = query.filter(TeamActivity.action == action)

    query = query.options(joinedload(TeamActivity.user))  # ✅ 유저 미리 로딩
    query = query.order_by(TeamActivity.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    return query.all()

async def get_recent_team_activities(
    db: Session,
    team_id: int,
    hours: int = 24,
    limit: int = 20
) -> List[TeamActivity]:
    """
    최근 팀 활동 로그 조회

    Args:
        db: 데이터베이스 세션
        team_id: 팀 ID
        hours: 최근 몇 시간 내의 활동을 조회할지
        limit: 최대 결과 수

    Returns:
        TeamActivity 객체 목록
    """
    start_date = datetime.utcnow() - timedelta(hours=hours)

    return await get_team_activities(
        db=db,
        team_id=team_id,
        start_date=start_date,
        limit=limit,
        page=1
    )

async def get_user_team_activities(
    db: Session,
    user_id: int,
    team_id: Optional[int] = None,
    days: int = 7,
    page: int = 1,
    limit: int = 50
) -> List[TeamActivity]:
    """
    특정 사용자의 팀 활동 로그 조회

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        team_id: 팀 ID (지정 시 해당 팀만 조회)
        days: 최근 몇 일 내의 활동을 조회할지
        page: 페이지 (1부터 시작)
        limit: 페이지당 결과 수

    Returns:
        TeamActivity 객체 목록
    """
    start_date = datetime.utcnow() - timedelta(days=days)

    query = db.query(TeamActivity).filter(TeamActivity.user_id == user_id)

    if team_id:
        query = query.filter(TeamActivity.team_id == team_id)

    query = query.filter(TeamActivity.created_at >= start_date)
    query = query.order_by(TeamActivity.created_at.desc())
    query = query.offset((page - 1) * limit).limit(limit)

    return query.all()