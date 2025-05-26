# app/handlers/signup_bonus.py

from sqlalchemy.orm import Session
from app.models.user import User
from app.models.event import Event, UserEvent
from app.services.point_service import add_points
from app.models.gamification import PointActionType


def handle_signup_bonus(
    db: Session,
    user: User,
    event_id: int,
    payload: dict
) -> dict:
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise ValueError("이벤트를 찾을 수 없습니다.")

    add_points(db, user.id, PointActionType.SIGNUP_BONUS, points=event.reward_points)

    user_event = UserEvent(
        user_id=user.id,
        event_id=event.id,
        is_completed=True,
        points_earned=event.reward_points,
        bonus_earned=event.bonus_points,
        event_data=payload
    )
    db.add(user_event)
    db.commit()

    return {
        "success": True,
        "message": "가입 이벤트 보상이 지급되었습니다.",
        "points_awarded": event.reward_points,
        "bonus_awarded": event.bonus_points
    }
