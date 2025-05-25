# app/handlers/invite_code.py

from sqlalchemy.orm import Session
from app.models.user import User
from app.models.event import Event, InviteCode, UserEvent
from app.services.point_service import add_points
from app.models.gamification import PointActionType


def handle_invite_code(
    db: Session,
    user: User,
    event_id: int,
    payload: dict
) -> dict:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise ValueError("이벤트를 찾을 수 없습니다.")

    code_str = payload.get("code")
    if not code_str:
        return {"success": False, "message": "초대 코드가 필요합니다."}

    code = db.query(InviteCode).filter_by(code=code_str, event_id=event.id).first()

    if not code or not code.is_valid:
        return {"success": False, "message": "유효하지 않은 초대 코드입니다."}

    if code.used_by_id:
        return {"success": False, "message": "이미 사용된 초대 코드입니다."}

    if user.id == code.inviter_id:
        return {"success": False, "message": "자기 자신의 코드는 사용할 수 없습니다."}

    code.use_code(user.id)
    db.add(code)

    add_points(db, user.id, PointActionType.INVITE_USED, points=event.reward_points)
    add_points(db, code.inviter_id, PointActionType.INVITE_SENT, points=event.bonus_points)

    user_event = UserEvent(
        user_id=user.id,
        event_id=event.id,
        is_completed=True,
        points_earned=event.reward_points,
        bonus_earned=event.bonus_points,
        event_data={"invite_code": code_str, "inviter_id": code.inviter_id}
    )
    db.add(user_event)
    db.commit()

    return {
        "success": True,
        "message": "초대 코드 사용 보상이 지급되었습니다.",
        "points_awarded": event.reward_points,
        "bonus_awarded": event.bonus_points
    }
