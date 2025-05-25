# app/services/point_service.py

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.models.user import User
from app.models.gamification import PointHistory, PointActionType, Badge, UserBadge
from app.schemas.gamification import PointSummary

import logging
logger = logging.getLogger(__name__)

# 레벨별 필요 포인트 정의
LEVEL_THRESHOLDS = {
    1: 0,
    2: 100,
    3: 300,
    4: 600,
    5: 1000,
    6: 1500,
    7: 2100,
    8: 2800,
    9: 3600,
    10: 4500
}

# 액션별 기본 포인트 정의
ACTION_POINTS = {
    PointActionType.ATTENDANCE: 10,
    PointActionType.ANNOTATION: 5,
    PointActionType.PDF_UPLOAD: 20,
    PointActionType.TEAM_CREATE: 50,
    PointActionType.TEAM_JOIN: 30,
    PointActionType.LEVEL_UP: 0,
    PointActionType.ADMIN: 0,
    PointActionType.EVENT: 0,
    PointActionType.QUEST: 0
}

def add_points(
    db: Session,
    user_id: int,
    action_type: PointActionType,
    points: Optional[int] = None,
    description: Optional[str] = None,
    reference_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    사용자에게 포인트를 추가하고 레벨업 확인
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"success": False, "error": "사용자를 찾을 수 없습니다"}

    if points is None:
        points = ACTION_POINTS.get(action_type, 0)

    if description is None:
        description_map = {
            PointActionType.ATTENDANCE: "출석 체크 보상",
            PointActionType.ANNOTATION: "PDF 주석 작성",
            PointActionType.PDF_UPLOAD: "PDF 업로드",
            PointActionType.TEAM_CREATE: "팀 생성",
            PointActionType.TEAM_JOIN: "팀 가입",
            PointActionType.LEVEL_UP: "레벨업 보너스",
            PointActionType.ADMIN: "관리자 지급",
            PointActionType.EVENT: "이벤트 보상",
            PointActionType.QUEST: "퀘스트 완료"
        }
        description = description_map.get(action_type, f"{action_type.value} 보상")

    prev_level = user.level

    point_history = PointHistory(
        user_id=user_id,
        action_type=action_type,
        points=points,
        description=description,
        reference_id=reference_id
    )
    db.add(point_history)

    user.points += points
    user.level = calculate_level(user.points)

    level_up = user.level > prev_level
    level_up_points = 0

    if level_up:
        level_up_points = user.level * 50
        level_up_history = PointHistory(
            user_id=user_id,
            action_type=PointActionType.LEVEL_UP,
            points=level_up_points,
            description=f"레벨 {user.level} 달성 보너스"
        )
        db.add(level_up_history)
        user.points += level_up_points

    logger.info("🧪 add_points called with action_type = %s (%s)", action_type, type(action_type))
    db.commit()
    
    return {
        "success": True,
        "points_added": points,
        "current_points": user.points,
        "level_up": level_up,
        "current_level": user.level,
        "level_up_points": level_up_points,
        "total_points_added": points + level_up_points
    }

def calculate_level(points: int) -> int:
    """포인트를 기준으로 현재 레벨 계산"""
    level = 1
    for lvl, threshold in sorted(LEVEL_THRESHOLDS.items()):
        if points >= threshold:
            level = lvl
        else:
            break
    return level

def get_points_to_next_level(current_points: int, current_level: int) -> int:
    """다음 레벨까지 필요한 포인트 계산"""
    next_level = current_level + 1
    if next_level not in LEVEL_THRESHOLDS:
        return 0
    return LEVEL_THRESHOLDS[next_level] - current_points

def get_point_summary(db: Session, user_id: int) -> PointSummary:
    """사용자의 포인트 요약 정보 조회"""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("사용자를 찾을 수 없습니다")

    points_to_next = get_points_to_next_level(user.points, user.level)

    if user.level < max(LEVEL_THRESHOLDS.keys()):
        current_level_points = LEVEL_THRESHOLDS[user.level]
        next_level_points = LEVEL_THRESHOLDS[user.level + 1]
        total_points_needed = next_level_points - current_level_points
        current_level_progress = user.points - current_level_points
        progress_percent = (current_level_progress / total_points_needed) * 100
    else:
        progress_percent = 100

    return PointSummary(
        total_points=user.points,
        current_level=user.level,
        points_to_next_level=points_to_next,
        level_progress_percent=progress_percent,
        streak_days=user.streak_days
    )

def get_point_history(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[PointHistory]:
    """사용자의 포인트 이력 조회"""
    return (
        db.query(PointHistory)
        .filter(PointHistory.user_id == user_id)
        .order_by(PointHistory.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
