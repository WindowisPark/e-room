# app/crud/crud_event.py

from sqlalchemy.orm import Session
from app.models.event import Event, EventType


def get_event_by_type(db: Session, event_type: EventType) -> Event:
    """
    이벤트 타입으로 활성 이벤트를 조회합니다.

    Args:
        db: 데이터베이스 세션
        event_type: 이벤트 타입

    Returns:
        Event 객체 또는 None
    """
    return (
        db.query(Event)
        .filter(Event.event_type == event_type)
        .order_by(Event.created_at.desc())  # 가장 최신 이벤트 우선
        .first()
    )
