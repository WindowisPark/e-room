# app/api/v1/endpoints/attendance.py (수정된 버전)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import date

from app import crud, schemas
from app.api import deps
from app.core.redis_helper import is_attendance_checked, mark_attendance
from app.services.notification_service import send_notification
from app.services.point_service import add_points, PointActionType  # 추가: 포인트 서비스

router = APIRouter()

@router.post("/", response_model=schemas.AttendanceResponse)
async def check_attendance(
    db: Session = Depends(deps.get_db),
    current_user: schemas.User = Depends(deps.get_current_user)
):
    """
    출석 체크 API
    - 하루에 한 번만 가능 (Redis 중복 방지)
    - 성공 시 DB 기록 + Redis 마킹 + 시스템 알림 전송
    - 추가: 포인트 적립
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
    attendance = crud.crud_attendance.upsert_attendance(db, user_id)
    mark_attendance(user_id)

    # 연속 출석일 업데이트
    current_streak = crud.crud_attendance.get_current_streak(db, user_id)
    current_user.streak_days = current_streak
    db.commit()

    # ✅ 포인트 적립 (기본 출석 포인트 + 연속 출석 보너스)
    base_points = 10  # 기본 출석 포인트
    bonus_points = 0

    # 연속 출석에 따른 보너스 포인트 계산
    if current_streak >= 30:
        bonus_points = 30  # 30일 이상 연속 출석
    elif current_streak >= 14:
        bonus_points = 20  # 14일 이상 연속 출석
    elif current_streak >= 7:
        bonus_points = 10  # 7일 이상 연속 출석
    elif current_streak >= 3:
        bonus_points = 5   # 3일 이상 연속 출석

    # 포인트 적립
    point_result = await add_points(
        db=db,
        user_id=user_id,
        action_type=PointActionType.ATTENDANCE,
        points=base_points + bonus_points,
        description=f"출석 체크 보상 (연속 {current_streak}일차)",
        reference_id=attendance.id
    )

    # ✅ 알림 전송 (포인트 내용 포함)
    bonus_text = f" (+{bonus_points} 연속 출석 보너스)" if bonus_points > 0 else ""
    await send_notification(
        db=db,
        user_id=user_id,
        type="system",
        message=f"출석 완료! {base_points + bonus_points}P 적립{bonus_text}",
        link="/attendance/history"
    )

    # 레벨업 알림
    if point_result.get("level_up"):
        await send_notification(
            db=db,
            user_id=user_id,
            type="system",
            message=f"축하합니다! 레벨 {point_result.get('current_level')}이 되었습니다! (+{point_result.get('level_up_points')}P 보너스)",
            link="/gamification/profile"
        )

    # 응답 반환
    return schemas.AttendanceResponse(
        success=True,
        message="출석이 완료되었습니다.",
        current_streak=current_streak,
        today_checked=True,
        today=date.today()
    )