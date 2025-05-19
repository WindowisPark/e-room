# app/api/v1/endpoints/badges.py

from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.api.deps import get_db, get_current_user, get_admin_user
from app.models.user import User
from app.services.badge_service import (
    check_and_award_badge,
    check_achievement_badges,
    get_user_badges,
    get_available_badges
)

router = APIRouter()

@router.get("/badges", response_model=List[Dict[str, Any]])
async def list_user_badges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    현재 사용자가 획득한 모든 배지 조회
    """
    badges = await get_user_badges(db, current_user.id)
    return badges

@router.get("/badges/available", response_model=List[Dict[str, Any]])
async def list_available_badges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    사용자가 아직 획득하지 않은 배지 목록 조회
    """
    badges = await get_available_badges(db, current_user.id)
    return badges

@router.post("/badges/check-achievements", response_model=Dict[str, Any])
async def check_badges(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    사용자의 활동과 성취를 확인하여 새로운 배지 부여
    """
    new_badges = await check_achievement_badges(db, current_user.id)
    return {
        "newly_acquired_badges": new_badges,
        "total_new_badges": len(new_badges)
    }

@router.post("/admin/award-badge", response_model=Dict[str, Any])
async def admin_award_badge(
    user_id: int = Query(..., description="배지를 부여할 사용자 ID"),
    badge_code: str = Query(..., description="부여할 배지 코드"),
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_admin_user)
):
    """
    관리자가 특정 사용자에게 배지 수여 (관리자 전용)
    """
    result = await check_and_award_badge(db, user_id, badge_code)

    if not result or not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "배지 부여 실패")
        )

    return result