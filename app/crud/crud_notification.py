# app/crud/crud_notification.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.models.notification import Notification

def create_notification(
    db: Session,
    user_id: int,
    type: str,  # mention, tag, chat, system 등
    message: str,
    link: Optional[str] = None
) -> Notification:
    """새 알림 생성"""
    db_notification = Notification(
        user_id=user_id,
        type=type,
        message=message,
        link=link,
        is_read=False
    )
    db.add(db_notification)
    db.commit()
    db.refresh(db_notification)
    return db_notification

def get_notifications_by_user(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    unread_only: bool = False
) -> List[Notification]:
    """사용자별 알림 목록 조회"""
    query = db.query(Notification).filter(Notification.user_id == user_id)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    
    return (
        query
        .order_by(desc(Notification.created_at))
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

def get_unread_notification_count(db: Session, user_id: int) -> int:
    """사용자의 읽지 않은 알림 수 조회"""
    return (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)
        .count()
    )

def mark_notification_as_read(db: Session, notification_id: int, user_id: int) -> bool:
    """특정 알림을 읽음 상태로 변경"""
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )
    
    if not notification:
        return False
    
    notification.is_read = True
    db.commit()
    return True

def mark_all_notifications_as_read(db: Session, user_id: int) -> int:
    """사용자의 모든 알림을 읽음 상태로 변경"""
    result = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)
        .update({"is_read": True})
    )
    
    db.commit()
    return result  # 업데이트된 알림 수 반환

def delete_notification(db: Session, notification_id: int, user_id: int) -> bool:
    """알림 삭제"""
    notification = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == user_id)
        .first()
    )
    
    if not notification:
        return False
    
    db.delete(notification)
    db.commit()
    return True

def delete_old_notifications(db: Session, days: int = 30) -> int:
    """일정 기간이 지난 알림 일괄 삭제"""
    import datetime
    
    cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
    
    result = (
        db.query(Notification)
        .filter(Notification.created_at < cutoff_date)
        .delete()
    )
    
    db.commit()
    return result  # 삭제된 알림 수 반환