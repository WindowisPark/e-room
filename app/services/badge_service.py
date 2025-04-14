# app/services/badge_service.py

from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.models.user import User
from app.models.gamification import Badge, UserBadge, BadgeType
from app.models.tag import PDFTag
from app.models.team import Team, TeamMember

async def check_and_award_badge(
    db: Session, 
    user_id: int, 
    badge_code: str
) -> Optional[Dict[str, Any]]:
    """
    사용자에게 배지 수여
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        badge_code: 배지 코드
        
    Returns:
        배지 수여 결과
    """
    # 사용자 조회
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return {"success": False, "error": "사용자를 찾을 수 없습니다"}
    
    # 배지 조회
    badge = db.query(Badge).filter(Badge.code == badge_code).first()
    if not badge:
        return {"success": False, "error": "배지를 찾을 수 없습니다"}
    
    # 배지 이미 보유 여부 확인
    existing_badge = db.query(UserBadge).filter(
        UserBadge.user_id == user_id,
        UserBadge.badge_id == badge.id
    ).first()
    
    if existing_badge:
        return {"success": False, "error": "이미 해당 배지를 보유하고 있습니다"}
    
    # 레벨 요구사항 확인
    if badge.required_level and user.level < badge.required_level:
        return {"success": False, "error": f"배지 획득에 필요한 레벨({badge.required_level})에 도달하지 않았습니다"}
    
    # 배지 부여
    user_badge = UserBadge(
        user_id=user_id,
        badge_id=badge.id
    )
    db.add(user_badge)
    db.commit()
    db.refresh(user_badge)
    
    # 알림 전송
    from app.services.notification_service import send_notification
    
    await send_notification(
        db=db,
        user_id=user_id,
        type="system",
        message=f"축하합니다! '{badge.name}' 배지를 획득했습니다!",
        link="/gamification/badges"
    )
    
    # 포인트 보상 (배지 획득 보너스)
    from app.services.point_service import add_points, PointActionType
    
    # 배지 타입에 따른 포인트 결정
    if badge.badge_type == BadgeType.LEVEL:
        points = 100  # 레벨 배지 (높은 보상)
    elif badge.badge_type in [BadgeType.ATTENDANCE, BadgeType.TEAM]:
        points = 50   # 출석/팀 배지 (중간 보상)
    else:
        points = 30   # 기타 배지 (기본 보상)
    
    point_result = await add_points(
        db=db,
        user_id=user_id,
        action_type=PointActionType.QUEST,
        points=points,
        description=f"배지 획득: {badge.name}",
        reference_id=user_badge.id
    )
    
    # 결과 반환
    return {
        "success": True,
        "badge": {
            "id": badge.id,
            "code": badge.code,
            "name": badge.name,
            "description": badge.description,
            "image_url": badge.image_url
        },
        "acquired_at": user_badge.acquired_at,
        "points_earned": points
    }

async def check_achievement_badges(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """
    사용자의 통계를 확인하여 획득 가능한 배지 확인 및 부여
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        
    Returns:
        새로 획득한 배지 목록
    """
    # 사용자 조회
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []
    
    # 이미 획득한 배지 코드 목록
    acquired_badge_ids = [ub.badge_id for ub in user.badges]
    acquired_badge_codes = [
        badge.code for badge in 
        db.query(Badge).filter(Badge.id.in_(acquired_badge_ids)).all()
    ]
    
    # 새로 획득한 배지 저장용
    newly_acquired_badges = []
    
    # 출석 관련 배지
    if user.streak_days >= 1 and "attendance_first" not in acquired_badge_codes:
        result = await check_and_award_badge(db, user_id, "attendance_first")
        if result and result.get("success"):
            newly_acquired_badges.append(result)
    
    if user.streak_days >= 7 and "attendance_week" not in acquired_badge_codes:
        result = await check_and_award_badge(db, user_id, "attendance_week")
        if result and result.get("success"):
            newly_acquired_badges.append(result)
    
    if user.streak_days >= 30 and "attendance_month" not in acquired_badge_codes:
        result = await check_and_award_badge(db, user_id, "attendance_month")
        if result and result.get("success"):
            newly_acquired_badges.append(result)
    
    # 주석 관련 배지
    annotation_count = db.query(PDFTag).filter(PDFTag.user_id == user_id).count()
    
    if annotation_count >= 1 and "annotation_first" not in acquired_badge_codes:
        result = await check_and_award_badge(db, user_id, "annotation_first")
        if result and result.get("success"):
            newly_acquired_badges.append(result)
    
    if annotation_count >= 100 and "annotation_master" not in acquired_badge_codes:
        result = await check_and_award_badge(db, user_id, "annotation_master")
        if result and result.get("success"):
            newly_acquired_badges.append(result)
    
    # 팀 관련 배지
    team_count = db.query(Team).filter(Team.owner_id == user_id).count()
    
    if team_count >= 1 and "team_creator" not in acquired_badge_codes:
        result = await check_and_award_badge(db, user_id, "team_creator")
        if result and result.get("success"):
            newly_acquired_badges.append(result)
    
    team_member_count = db.query(TeamMember).filter(TeamMember.user_id == user_id).count()
    
    if team_member_count >= 5 and "team_collaborator" not in acquired_badge_codes:
        result = await check_and_award_badge(db, user_id, "team_collaborator")
        if result and result.get("success"):
            newly_acquired_badges.append(result)
    
    # 레벨 관련 배지
    if user.level >= 5 and "level_5" not in acquired_badge_codes:
        result = await check_and_award_badge(db, user_id, "level_5")
        if result and result.get("success"):
            newly_acquired_badges.append(result)
    
    if user.level >= 10 and "level_10" not in acquired_badge_codes:
        result = await check_and_award_badge(db, user_id, "level_10")
        if result and result.get("success"):
            newly_acquired_badges.append(result)
    
    return newly_acquired_badges

async def get_user_badges(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """
    사용자가 획득한 배지 목록 조회
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        
    Returns:
        배지 목록
    """
    user_badges = db.query(UserBadge).filter(UserBadge.user_id == user_id).all()
    
    result = []
    for user_badge in user_badges:
        badge = user_badge.badge
        result.append({
            "id": badge.id,
            "code": badge.code,
            "name": badge.name,
            "description": badge.description,
            "image_url": badge.image_url,
            "badge_type": badge.badge_type,
            "acquired_at": user_badge.acquired_at
        })
    
    return result

async def get_available_badges(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """
    사용자가 획득할 수 있는 배지 목록 조회
    
    Args:
        db: 데이터베이스 세션
        user_id: 사용자 ID
        
    Returns:
        배지 목록
    """
    # 사용자 조회
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return []
    
    # 이미 획득한 배지 ID 목록
    acquired_badge_ids = [ub.badge_id for ub in user.badges]
    
    # 획득하지 않은 모든 배지 조회
    available_badges = db.query(Badge).filter(~Badge.id.in_(acquired_badge_ids)).all()
    
    result = []
    for badge in available_badges:
        # 레벨 요구사항 충족 여부 확인
        is_eligible = True
        reason = None
        
        if badge.required_level and user.level < badge.required_level:
            is_eligible = False
            reason = f"레벨 {badge.required_level} 이상 필요 (현재 레벨: {user.level})"
        
        result.append({
            "id": badge.id,
            "code": badge.code,
            "name": badge.name,
            "description": badge.description,
            "image_url": badge.image_url,
            "badge_type": badge.badge_type,
            "is_eligible": is_eligible,
            "reason": reason
        })
    
    return result