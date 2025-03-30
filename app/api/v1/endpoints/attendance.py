# app/api/v1/endpoints/attendance.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date

from app import crud, schemas
from app.api import deps
from app.core.redis_helper import is_attendance_checked, mark_attendance
from app.services.notification_service import send_notification  # ✅ 알림 서비스 import

router = APIRouter()

@router.post("/attendance", response_model=schemas.AttendanceResponse)
async def check_attendance(
    db: Session = Depends(deps.get_db),
    current_user: schemas.User = Depends(deps.get_current_user)
):
    """
    출석 체크 API
    - 하루에 한 번만 가능 (Redis 중복 방지)
    - 성공 시 DB 기록 + Redis 마킹 + 시스템 알림 전송
    """
    user_id = current_user.id

    # 이미 출석한 경우
    if is_attendance_checked(user_id):
        return schemas.AttendanceResponse(
            success=False,
            message="이미 출석했습니다.",
            current_streak=crud.crud_attendance.get_current_streak(db, user_id),
            today_checked=True,
            today=date.today()
        )

    # 출석 처리 (DB + Redis)
    crud.crud_attendance.upsert_attendance(db, user_id)
    mark_attendance(user_id)

    # ✅ 알림 전송
    await send_notification(
        db=db,
        user_id=user_id,
        type="system",
        message="오늘 출석이 완료되었습니다!",
        link="/attendance/history"
    )

    # 응답 반환
    return schemas.AttendanceResponse(
        success=True,
        message="출석이 완료되었습니다.",
        current_streak=crud.crud_attendance.get_current_streak(db, user_id),
        today_checked=True,
        today=date.today()
    )
