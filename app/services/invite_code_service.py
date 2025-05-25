# app/services/invite_code_service.py

import secrets
from sqlalchemy.orm import Session
from app.models.event import InviteCode, Event
from app.models.user import User


def create_invite_code(
    db: Session,
    inviter: User,
    event: Event,
    max_uses: int = 1,
    expires_at: str = None
) -> InviteCode:
    """
    초대 코드를 생성합니다.
    """
    code = secrets.token_urlsafe(6).upper()

    invite_code = InviteCode(
        code=code,
        inviter_id=inviter.id,
        event_id=event.id,
        max_uses=max_uses,
        expires_at=expires_at
    )
    db.add(invite_code)
    db.commit()
    db.refresh(invite_code)
    return invite_code


def get_invite_codes_by_user(db: Session, user_id: int) -> list[InviteCode]:
    """
    사용자가 생성한 초대 코드 목록 조회
    """
    return (
        db.query(InviteCode)
        .filter(InviteCode.inviter_id == user_id)
        .order_by(InviteCode.created_at.desc())
        .all()
    )


def get_valid_invite_code(db: Session, code: str) -> InviteCode | None:
    """
    유효한 초대 코드 조회
    """
    invite = db.query(InviteCode).filter(InviteCode.code == code).first()
    return invite if invite and invite.is_valid else None
