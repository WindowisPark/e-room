# app/services/point_service.py

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.models.user import User
from app.models.gamification import PointHistory, PointActionType, Badge, UserBadge
from app.schemas.gamification import PointHistoryCreate, PointSummary

# 레벨별 필요 포인트 정의 (레벨:필요 포인트)
LEVEL_THRESHOLDS = {
    1: 0,      # 레벨 1 (시작)
    2: 100,    # 레벨 2가 되기 위한 최소 포인트
    3: 300,    # 레벨 3가 되기 위한 최소 포인트
    4: 600,    # 레벨 4가 되기 위한 최소 포인트
    5: 1000,   # 레벨 5가 되기 위한 최소 포인트
    6: 1500,   # 레벨 6가 되기 위한 최소 포인트
    7: 2100,   # 레벨 7가 되기 위한 최소 포인트
    8: 2800,   # 레벨 8가 되기 위한 최소 포인트
    9: 3600,   # 레벨 9가 되기 위한 최소 포인트
    10: 4500   # 레벨 10가 되기 위한 최소 포인트
}

# 액션별 기본 포인트 정의
ACTION_POINTS = {
    PointActionType.ATTENDANCE: 10,      # 출석 체크
    PointActionType.ANNOTATION: 5,       # PDF 주석 작성
    PointActionType.PDF_UPLOAD: 20,      # PDF 업로드
    PointActionType.TEAM_CREATE: 50,     # 팀 생성
    PointActionType.TEAM_JOIN: 30,       # 팀 가입
    PointActionType.LEVEL_UP: 0,         # 레벨업 (보상 별도 계산)
    PointActionType.ADMIN: 0,            # 관리자 지급 (값 별도 지정)
    PointActionType.EVENT: 0,            # 이벤트 보상 (값 별도 지정)
    PointActionType.QUEST: 0             # 퀘스트 완료 (값 별도 지정)
}

async def add_points(
    db: Session,
    user_id: int,
    action_type: PointActionType,
    points: Optional[int] = None,
    description: Optional[str] = None,
    reference_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    사용자에게 포인트를 추가하고 레벨업 확인

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        action_type: 포인트 적립 액션 타입
        points: 지급할 포인트 (None인 경우 액션 기본값 사용)
        description: 포인트 적립 설명 (None인 경우 액션 타입으로 자동 생성)
        reference_id: 관련 엔티티 ID (예: 주석 ID)

    Returns:
        처리 결과 (포인트 적립 정보, 레벨업 여부 등)
    """
    # 사용자 조회
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"success": False, "error": "사용자를 찾을 수 없습니다"}

    # 포인트 결정
    if points is None:
        points = ACTION_POINTS.get(action_type, 0)

    # 설명 자동 생성
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

    # 이전 레벨 저장
    prev_level = user.level

    # 포인트 내역 생성
    point_history = PointHistory(
        user_id=user_id,
        action_type=action_type,
        points=points,
        description=description,
        reference_id=reference_id
    )
    db.add(point_history)

    # 사용자 포인트 업데이트
    user.points += points

    # 레벨 계산
    user.level = calculate_level(user.points)

    # 레벨업 확인 및 보너스 포인트 지급
    level_up = user.level > prev_level
    level_up_points = 0

    if level_up:
        # 레벨업 보너스 포인트 (레벨 * 50)
        level_up_points = user.level * 50

        # 레벨업 보너스 내역 추가
        level_up_history = PointHistory(
            user_id=user_id,
            action_type=PointActionType.LEVEL_UP,
            points=level_up_points,
            description=f"레벨 {user.level} 달성 보너스"
        )
        db.add(level_up_history)

        # 보너스 포인트 적용
        user.points += level_up_points

    # 변경사항 저장
    db.commit()

    # 결과 반환
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
    """
    포인트를 기준으로 레벨 계산

    Args:
        points: 현재 포인트

    Returns:
        현재 레벨
    """
    level = 1
    for lvl, threshold in sorted(LEVEL_THRESHOLDS.items()):
        if points >= threshold:
            level = lvl
        else:
            break
    return level

def get_points_to_next_level(current_points: int, current_level: int) -> int:
    """
    다음 레벨까지 필요한 포인트 계산

    Args:
        current_points: 현재 포인트
        current_level: 현재 레벨

    Returns:
        다음 레벨까지 필요한 포인트
    """
    next_level = current_level + 1
    if next_level not in LEVEL_THRESHOLDS:
        return 0  # 최대 레벨인 경우

    next_level_threshold = LEVEL_THRESHOLDS[next_level]
    return next_level_threshold - current_points

def get_point_summary(db: Session, user_id: int) -> PointSummary:
    """
    사용자의 포인트 요약 정보 조회

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID

    Returns:
        포인트 요약 정보
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise ValueError("사용자를 찾을 수 없습니다")

    points_to_next = get_points_to_next_level(user.points, user.level)

    # 다음 레벨이 있는 경우 진행률 계산
    if user.level < max(LEVEL_THRESHOLDS.keys()):
        current_level_points = LEVEL_THRESHOLDS[user.level]
        next_level_points = LEVEL_THRESHOLDS[user.level + 1]
        total_points_needed = next_level_points - current_level_points
        current_level_progress = user.points - current_level_points
        progress_percent = (current_level_progress / total_points_needed) * 100
    else:
        # 최대 레벨인 경우
        progress_percent = 100

    return PointSummary(
        total_points=user.points,
        current_level=user.level,
        points_to_next_level=points_to_next,
        level_progress_percent=progress_percent,
        streak_days=user.streak_days
    )

def get_point_history(db: Session, user_id: int, skip: int = 0, limit: int = 50) -> List[PointHistory]:
    """
    사용자의 포인트 이력 조회

    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        skip: 건너뛸 레코드 수
        limit: 최대 조회 레코드 수

    Returns:
        포인트 이력 목록
    """
    return db.query(PointHistory)\
        .filter(PointHistory.user_id == user_id)\
        .order_by(PointHistory.created_at.desc())\
        .offset(skip).limit(limit)\
        .all()