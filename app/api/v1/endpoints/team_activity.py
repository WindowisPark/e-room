# app/api/v1/endpoints/team_activity.py

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.collaboration import TeamActivityLog
from app.services.team_service import check_team_permission
from app.services.team_activity_service import (
    get_team_activities,
    get_recent_team_activities,
    get_user_team_activities
)

router = APIRouter()

@router.get("/{team_id}/activities", response_model=List[TeamActivityLog])
async def list_team_activities(
    team_id: int = Path(..., ge=1),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    user_id: Optional[int] = None,
    resource_type: Optional[str] = None,
    action: Optional[str] = None,
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    팀 활동 로그 조회 (필터링 및 페이지네이션 지원)
    """
    # 팀 멤버십 확인
    has_access = await check_team_permission(
        db=db,
        team_id=team_id,
        user_id=current_user.id
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 팀스페이스의 활동 로그를 조회할 권한이 없습니다"
        )

    activities = await get_team_activities(
        db=db,
        team_id=team_id,
        start_date=start_date,
        end_date=end_date,
        user_id=user_id,
        resource_type=resource_type,
        action=action,
        page=page,
        limit=limit
    )

    return activities

@router.get("/{team_id}/activities/recent", response_model=List[TeamActivityLog])
async def get_recent_activities(
    team_id: int = Path(..., ge=1),
    hours: int = Query(24, ge=1, le=168),  # 최대 1주일(168시간)
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    최근 팀 활동 로그 조회
    """
    # 팀 멤버십 확인
    has_access = await check_team_permission(
        db=db,
        team_id=team_id,
        user_id=current_user.id
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 팀스페이스의 활동 로그를 조회할 권한이 없습니다"
        )

    activities = await get_recent_team_activities(
        db=db,
        team_id=team_id,
        hours=hours,
        limit=limit
    )

    return activities

@router.get("/activities/me", response_model=List[TeamActivityLog])
async def get_my_team_activities(
    team_id: Optional[int] = None,
    days: int = Query(7, ge=1, le=30),  # 최대 30일
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    내 팀 활동 로그 조회
    """
    # 특정 팀이 지정된 경우 멤버십 확인
    if team_id:
        has_access = await check_team_permission(
            db=db,
            team_id=team_id,
            user_id=current_user.id
        )
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="이 팀스페이스의 활동 로그를 조회할 권한이 없습니다"
            )

    activities = await get_user_team_activities(
        db=db,
        user_id=current_user.id,
        team_id=team_id,
        days=days,
        page=page,
        limit=limit
    )

    return activities

@router.post("/{team_id}/activities/test-log")
async def create_test_log(
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    🔧 테스트용 로그 생성 엔드포인트
    """
    from app.services.team_activity_service import log_team_activity

    await log_team_activity(
        db=db,
        team_id=team_id,
        user_id=current_user.id,
        action="test",
        resource_type="test_resource",
        resource_id=None,
        details={"message": "테스트 로그입니다."}
    )
    return {"message": "✅ 테스트 로그가 성공적으로 저장되었습니다."}