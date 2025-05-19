# app/api/v1/endpoints/gamification.py

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.deps import get_db, get_current_user, get_admin_user
from app.models.user import User
from app.services.point_service import (
    add_points,
    get_point_summary,
    get_point_history,
    PointActionType
)
from app.schemas.gamification import (
    PointHistoryResponse,
    PointSummary,
    UserGamificationProfile,
    UserBadgeResponse
)

router = APIRouter()

@router.get("/points", response_model=PointSummary)
async def get_points(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    현재 사용자의 포인트 요약 정보 조회
    """
    try:
        return get_point_summary(db, current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/points/history", response_model=List[PointHistoryResponse])
async def get_points_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    현재 사용자의 포인트 이력 조회
    """
    history = get_point_history(db, current_user.id, skip, limit)
    return history

@router.post("/points/admin-add")
async def admin_add_points(
    user_id: int = Body(...),
    points: int = Body(...),
    description: str = Body(...),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    관리자가 특정 사용자에게 포인트 지급
    """
    result = await add_points(
        db=db,
        user_id=user_id,
        action_type=PointActionType.ADMIN,
        points=points,
        description=description
    )

    if not result.get("success"):
        raise HTTPException(status_code=404, detail=result.get("error"))

    return result

@router.get("/profile", response_model=UserGamificationProfile)
async def get_gamification_profile(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    현재 사용자의 게이미피케이션 프로필 조회
    (포인트, 레벨, 배지 등 종합 정보)
    """
    try:
        # 포인트 요약 정보 조회
        point_summary = get_point_summary(db, current_user.id)

        # 배지 정보 조회 (아직 구현되지 않음)
        # 구현 후 실제 데이터로 교체 필요
        badges = []

        return {
            "user_id": current_user.id,
            "username": current_user.username,
            "points": current_user.points,
            "level": current_user.level,
            "level_progress": point_summary.level_progress_percent,
            "streak_days": current_user.streak_days,
            "badges_count": len(badges),
            "recent_badges": badges
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))