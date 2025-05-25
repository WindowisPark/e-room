# app/services/event_service.py

import logging
from typing import Dict, Any
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.event import EventType, Event
from app.models.user import User
from app.models.event import UserEvent
from app.schemas.event import EventClaimRequest
from app.crud.crud_event import get_event_by_type
from app.services.point_service import add_points
from app.models.gamification import PointActionType
from app.handlers import signup_bonus, invite_code  # 이벤트 핸들러 모듈 import

logger = logging.getLogger(__name__)

# 이벤트 타입에 따른 핸들러 매핑
HANDLER_MAP = {
    EventType.SIGNUP_BONUS: signup_bonus.handle_signup_bonus,
    EventType.INVITE_CODE: invite_code.handle_invite_code,
}

def process_event(
    db: Session,
    user: User,
    request: EventClaimRequest
) -> Dict[str, Any]:
    """
    이벤트 처리의 통합 서비스
    - 이벤트 조회
    - 중복 참여 여부 확인
    - 핸들러 디스패치 및 결과 반환
    """
    event = get_event_by_type(db, request.event_type)

    if not event:
        raise HTTPException(status_code=404, detail="해당 이벤트가 존재하지 않습니다.")

    if not event.is_active:
        raise HTTPException(status_code=400, detail="이벤트가 현재 활성화되어 있지 않습니다.")

    if not event.is_repeatable:
        existing = db.query(UserEvent).filter_by(user_id=user.id, event_id=event.id, is_completed=True).first()
        if existing:
            return {"success": False, "message": "이미 참여한 이벤트입니다."}

    handler = HANDLER_MAP.get(request.event_type)
    if not handler:
        raise HTTPException(status_code=400, detail="지원되지 않는 이벤트입니다.")

    # 실제 이벤트 처리
    result = handler(db=db, user=user, event_id=event.id, payload=request.payload)

    logger.info("🧪 DEBUG: event_type: %s", request.event_type)
    logger.info("🧪 DEBUG: handler result: %s", result)

    return result

def delete_event(db: Session, event_id: int, current_user: User):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="해당 이벤트를 찾을 수 없습니다.")
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 이벤트를 삭제할 수 있습니다.")

    db.delete(event)
    db.commit()
    return {"message": f"'{event.name}' 이벤트가 삭제되었습니다."}

def update_event(
    db: Session,
    event_id: int,
    updates: Dict[str, Any],
    current_user: User
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="해당 이벤트를 찾을 수 없습니다.")
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 이벤트를 수정할 수 있습니다.")

    for key, value in updates.items():
        if hasattr(event, key):
            setattr(event, key, value)

    db.commit()
    db.refresh(event)
    return {
        "message": f"'{event.name}' 이벤트가 수정되었습니다.",
        "event": {
            "id": event.id,
            "name": event.name,
            "status": event.status,
            "reward_points": event.reward_points,
            "bonus_points": event.bonus_points,
            "is_repeatable": event.is_repeatable,
            "max_participants": event.max_participants
        }
    }
