# app/api/v1/endpoints/events.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime

from app.api import deps
from app.models.user import User
from app.models.event import EventType, InviteCode, Event, EventStatus
from app.schemas.event import EventClaimRequest, EventClaimResponse
from app.services.event_service import process_event
from app.services.invite_code_service import create_invite_code, get_invite_codes_by_user, get_valid_invite_code
from app.crud.crud_event import get_event_by_type
from app.services.event_service import update_event 
from app.services.event_service import delete_event

router = APIRouter()

@router.post("/claim", response_model=EventClaimResponse, summary="이벤트 참여 처리")
def claim_event(
    request: EventClaimRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    try:
        result = process_event(db=db, user=current_user, request=request)
        return EventClaimResponse(**result)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"이벤트 처리 중 오류 발생: {str(e)}")


@router.post("/invite-code/generate", summary="초대 코드 생성")
def generate_invite_code(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    event = get_event_by_type(db, EventType.INVITE_CODE)
    if not event:
        raise HTTPException(status_code=404, detail="초대 이벤트가 존재하지 않습니다.")

    existing_code = (
        db.query(InviteCode)
        .filter(
            InviteCode.inviter_id == current_user.id,
            InviteCode.event_id == event.id,
            InviteCode.current_uses < InviteCode.max_uses
        )
        .order_by(InviteCode.created_at.desc())
        .first()
    )

    if existing_code:
        return {
            "code": existing_code.code,
            "max_uses": existing_code.max_uses,
            "expires_at": existing_code.expires_at
        }

    total_issued = db.query(InviteCode).filter(
        InviteCode.inviter_id == current_user.id,
        InviteCode.event_id == event.id
    ).count()

    if total_issued >= 3:
        raise HTTPException(status_code=400, detail="초대 코드는 최대 3개까지만 생성할 수 있습니다.")

    code = create_invite_code(db=db, inviter=current_user, event=event)
    return {
        "code": code.code,
        "max_uses": code.max_uses,
        "expires_at": code.expires_at
    }


@router.get("/invite-code/my", summary="내 초대 코드 목록 조회")
def get_my_invite_codes(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    codes = get_invite_codes_by_user(db=db, user_id=current_user.id)
    return [
        {
            "code": c.code,
            "created_at": c.created_at,
            "is_used": c.is_used,
            "current_uses": c.current_uses,
            "max_uses": c.max_uses,
            "expires_at": c.expires_at
        } for c in codes
    ]


@router.get("/invite-code/validate", summary="초대 코드 유효성 확인")
def validate_invite_code(
    code: str = Query(..., description="확인할 초대 코드"),
    db: Session = Depends(deps.get_db)
):
    invite = get_valid_invite_code(db, code)
    if not invite:
        return {"valid": False, "message": "유효하지 않거나 사용된 초대 코드입니다."}

    inviter_name = invite.inviter.username if invite.inviter else None
    return {
        "valid": True,
        "message": "사용 가능한 초대 코드입니다.",
        "inviter_name": inviter_name
    }


@router.post("/create", summary="이벤트 생성 (관리자 전용)")
def create_event(
    name: str,
    event_type: EventType,
    description: str = "",
    reward_points: int = 0,
    bonus_points: int = 0,
    is_repeatable: bool = False,
    max_participants: int = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    event = Event(
        name=name,
        event_type=event_type,
        description=description,
        start_date=datetime.utcnow(),
        end_date=None,
        status=EventStatus.ACTIVE,
        is_repeatable=is_repeatable,
        max_participants=max_participants,
        reward_points=reward_points,
        bonus_points=bonus_points,
        created_by=current_user.id
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"message": f"'{event.name}' 이벤트가 생성되었습니다.", "event_id": event.id}


@router.delete("/{event_id}", summary="이벤트 삭제 (관리자 전용)")
def delete_event(
    event_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="해당 이벤트를 찾을 수 없습니다.")
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="관리자만 이벤트를 삭제할 수 있습니다.")

    db.delete(event)
    db.commit()
    return {"message": f"'{event.name}' 이벤트가 삭제되었습니다."}

@router.put("/{event_id}", summary="이벤트 수정 (관리자 전용)")
def update_event_endpoint(
    event_id: int,
    updates: dict,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    return update_event(db=db, event_id=event_id, updates=updates, current_user=current_user)

@router.delete("/{event_id}", summary="이벤트 삭제 (관리자 전용)")
def delete_event_endpoint(
    event_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    return delete_event(db=db, event_id=event_id, current_user=current_user)