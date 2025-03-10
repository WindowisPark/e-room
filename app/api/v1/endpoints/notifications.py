# app/api/v1/endpoints/notifications.py
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.notification import NotificationResponse
from app.crud.crud_notification import (
    get_notifications_by_user,
    get_unread_notification_count,
    mark_notification_as_read,
    mark_all_notifications_as_read,
    delete_notification
)

router = APIRouter()

@router.get("/", response_model=List[NotificationResponse])
async def get_notifications(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    unread_only: bool = Query(False),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """사용자의 알림 목록 조회"""
    notifications = get_notifications_by_user(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        unread_only=unread_only
    )
    
    return [
        {
            "id": notification.id,
            "type": notification.type,
            "message": notification.message,
            "link": notification.link,
            "is_read": notification.is_read,
            "created_at": notification.created_at
        }
        for notification in notifications
    ]

@router.get("/count", response_model=Dict[str, int])
async def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """읽지 않은 알림 수 조회"""
    count = get_unread_notification_count(db=db, user_id=current_user.id)
    return {"unread_count": count}

@router.put("/{notification_id}/read", response_model=Dict[str, bool])
async def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """알림을 읽음 상태로 변경"""
    success = mark_notification_as_read(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="알림을 찾을 수 없습니다"
        )
    
    return {"success": True}

@router.put("/read-all", response_model=Dict[str, int])
async def mark_all_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """모든 알림을 읽음 상태로 변경"""
    count = mark_all_notifications_as_read(db=db, user_id=current_user.id)
    return {"marked_count": count}

@router.delete("/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_one_notification(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """알림 삭제"""
    success = delete_notification(
        db=db,
        notification_id=notification_id,
        user_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="알림을 찾을 수 없습니다"
        )