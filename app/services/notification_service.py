# app/services/notification_service.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.crud.crud_notification import create_notification
from app.crud.crud_team import check_user_in_team
from app.models.user import User
from app.core.redis_helper import get_redis_client

async def create_mention_notifications(
    db: Session,
    tag_id: int,
    team_id: Optional[int],
    mentioned_usernames: List[str],
    mentioner_id: int
) -> List[int]:
    """멘션된 사용자들에게 알림 생성"""
    # 멘션한 사용자 조회
    mentioner = db.query(User).filter(User.id == mentioner_id).first()
    if not mentioner:
        return []
    
    # 알림 생성된 사용자 ID 목록
    notified_user_ids = []
    
    for username in mentioned_usernames:
        # 멘션된 사용자 조회
        mentioned_user = db.query(User).filter(User.username == username).first()
        if not mentioned_user:
            continue
        
        # 팀스페이스가 있는 경우, 해당 팀의 멤버인지 확인
        if team_id and not check_user_in_team(db, team_id, mentioned_user.id):
            continue
        
        # 자기 자신을 멘션한 경우는 알림 생성하지 않음
        if mentioned_user.id == mentioner_id:
            continue
        
        # 알림 메시지 생성
        message = f"{mentioner.username}님이 문서에서 회원님을 멘션했습니다: @{username}"
        link = f"/pdf/{team_id}/tag/{tag_id}" if team_id else f"/tag/{tag_id}"
        
        # 알림 생성
        notification = create_notification(
            db=db,
            user_id=mentioned_user.id,
            type="mention",
            message=message,
            link=link
        )
        
        # 실시간 알림 발송
        redis_client = get_redis_client()
        await redis_client.publish(
            f"user:{mentioned_user.id}",
            {
                "type": "notification",
                "notification_id": notification.id,
                "message": message,
                "notification_type": "mention",
                "link": link,
                "created_at": notification.created_at.isoformat()
            }
        )
        
        notified_user_ids.append(mentioned_user.id)
    
    return notified_user_ids

async def create_chat_notification(
    db: Session,
    conversation_id: int,
    sender_id: int,
    message_content: str,
    receiver_id: int
) -> Optional[int]:
    """채팅 메시지 알림 생성"""
    # 발신자 조회
    sender = db.query(User).filter(User.id == sender_id).first()
    if not sender:
        return None
    
    # 수신자가 발신자와 같은 경우 알림 생성하지 않음
    if sender_id == receiver_id:
        return None
    
    # 메시지 내용 요약 (50자 제한)
    summary = message_content
    if len(summary) > 50:
        summary = summary[:47] + "..."
    
    # 알림 메시지 생성
    message = f"{sender.username}님의 메시지: {summary}"
    link = f"/chat/{conversation_id}"
    
    # 알림 생성
    notification = create_notification(
        db=db,
        user_id=receiver_id,
        type="chat",
        message=message,
        link=link
    )
    
    # 실시간 알림 발송
    redis_client = get_redis_client()
    await redis_client.publish(
        f"user:{receiver_id}",
        {
            "type": "notification",
            "notification_id": notification.id,
            "message": message,
            "notification_type": "chat",
            "link": link,
            "conversation_id": conversation_id,
            "sender_id": sender_id,
            "sender_name": sender.username,
            "created_at": notification.created_at.isoformat()
        }
    )
    
    return notification.id

async def create_team_invitation_notification(
    db: Session,
    team_id: int,
    team_name: str,
    inviter_id: int,
    invitee_id: int
) -> Optional[int]:
    """팀 초대 알림 생성"""
    # 초대자 조회
    inviter = db.query(User).filter(User.id == inviter_id).first()
    if not inviter:
        return None
    
    # 알림 메시지 생성
    message = f"{inviter.username}님이 '{team_name}' 팀에 초대했습니다"
    link = f"/teams/invitation/{team_id}"
    
    # 알림 생성
    notification = create_notification(
        db=db,
        user_id=invitee_id,
        type="team_invitation",
        message=message,
        link=link
    )
    
    # 실시간 알림 발송
    redis_client = get_redis_client()
    await redis_client.publish(
        f"user:{invitee_id}",
        {
            "type": "notification",
            "notification_id": notification.id,
            "message": message,
            "notification_type": "team_invitation",
            "team_id": team_id,
            "team_name": team_name,
            "inviter_id": inviter_id,
            "inviter_name": inviter.username,
            "link": link,
            "created_at": notification.created_at.isoformat()
        }
    )
    
    return notification.id

async def create_system_notification(
    db: Session,
    user_id: int,
    message: str,
    link: Optional[str] = None
) -> Optional[int]:
    """시스템 알림 생성"""
    # 알림 생성
    notification = create_notification(
        db=db,
        user_id=user_id,
        type="system",
        message=message,
        link=link
    )
    
    # 실시간 알림 발송
    redis_client = get_redis_client()
    await redis_client.publish(
        f"user:{user_id}",
        {
            "type": "notification",
            "notification_id": notification.id,
            "message": message,
            "notification_type": "system",
            "link": link,
            "created_at": notification.created_at.isoformat()
        }
    )
    
    return notification.id