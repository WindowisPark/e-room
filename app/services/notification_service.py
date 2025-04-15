# app/services/notification_service.py

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.crud.crud_notification import create_notification
from app.crud.crud_team import check_user_in_team
from app.models.user import User
from app.models.tag import PDFTagMention  # ✅ 멘션 중복 확인용
from app.core.redis_helper import get_redis_client

import json

# ✅ 공통 알림 생성 및 실시간 발송 함수
async def send_notification(
    db: Session,
    user_id: int,
    type: str,
    message: str,
    link: Optional[str] = None,
    extra_payload: Optional[Dict[str, Any]] = None
) -> Optional[int]:
    notification = create_notification(
        db=db,
        user_id=user_id,
        type=type,
        message=message,
        link=link
    )

    payload = {
        "type": "notification",
        "notification_id": notification.id,
        "message": message,
        "notification_type": type,
        "link": link,
        "created_at": notification.created_at.isoformat()
    }

    if extra_payload:
        payload.update(extra_payload)

    redis_client = get_redis_client()
    
    # 딕셔너리를 JSON 문자열로 변환하여 전송
    await redis_client.publish(f"user:{user_id}", json.dumps(payload))

    return notification.id


# ✅ 멘션 알림 (중복 방지 + 알림 수신 설정 반영)
async def create_mention_notifications(
    db: Session,
    tag_id: int,
    team_id: Optional[int],
    mentioned_usernames: List[str],
    mentioner_id: int
) -> List[int]:
    mentioner = db.query(User).filter(User.id == mentioner_id).first()
    if not mentioner:
        return []

    notified_user_ids = []

    for username in mentioned_usernames:
        mentioned_user = db.query(User).filter(User.username == username).first()
        if not mentioned_user:
            continue

        # ✅ 알림 수신 설정 체크
        if not mentioned_user.allow_mention_notifications:
            continue

        # ✅ 중복 알림 방지
        existing = db.query(PDFTagMention).filter_by(
            tag_id=tag_id,
            mentioned_user_id=mentioned_user.id
        ).first()

        if existing and existing.notification_sent:
            continue

        if not existing:
            mention = PDFTagMention(tag_id=tag_id, mentioned_user_id=mentioned_user.id)
            db.add(mention)
            db.commit()
        else:
            mention = existing

        # ✅ 알림 메시지 및 링크
        message = f"{mentioner.username}님이 문서에서 회원님을 멘션했습니다: @{username}"
        link = f"/pdf/{team_id}/tag/{tag_id}" if team_id else f"/tag/{tag_id}"

        await send_notification(
            db=db,
            user_id=mentioned_user.id,
            type="mention",
            message=message,
            link=link
        )

        # ✅ 알림 전송 완료 표시
        mention.notification_sent = True
        db.commit()

        notified_user_ids.append(mentioned_user.id)

    return notified_user_ids


# ✅ 팀 초대 알림
async def create_team_invitation_notification(
    db: Session,
    team_id: int,
    team_name: str,
    inviter_id: int,
    invitee_id: int
) -> Optional[int]:
    inviter = db.query(User).filter(User.id == inviter_id).first()
    if not inviter:
        return None

    message = f"{inviter.username}님이 '{team_name}' 팀에 초대했습니다"
    link = f"/teams/invitation/{team_id}"

    return await send_notification(
        db=db,
        user_id=invitee_id,
        type="team_invitation",
        message=message,
        link=link,
        extra_payload={
            "team_id": team_id,
            "team_name": team_name,
            "inviter_id": inviter_id,
            "inviter_name": inviter.username
        }
    )


# ✅ 시스템 알림
async def create_system_notification(
    db: Session,
    user_id: int,
    message: str,
    link: Optional[str] = None
) -> Optional[int]:
    return await send_notification(
        db=db,
        user_id=user_id,
        type="system",
        message=message,
        link=link
    )
