# app/crud/crud_attendance.py

from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.attendance import Attendance

def upsert_attendance(db: Session, user_id: int) -> Attendance:
    """
    오늘 날짜에 해당 사용자의 출석이 이미 있는지 확인
    - 없으면 새 출석 데이터를 생성
    - 있으면 기존 출석 기록 반환
    """
    today = date.today()
    record = (
        db.query(Attendance)
        .filter(and_(Attendance.user_id == user_id, Attendance.attendance_date == today))
        .first()
    )
    if record:
        return record

    new_record = Attendance(user_id=user_id, attendance_date=today)
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return new_record

def get_current_streak(db: Session, user_id: int, limit: int = 7) -> int:
    """
    최대 limit일 동안의 연속 출석 일수를 계산
    - 오늘부터 1일씩 거슬러 올라가며 출석 기록 확인
    - 출석이 끊기면 루프 종료
    """
    today = date.today()
    streak = 0
    for i in range(limit):
        check_date = today - timedelta(days=i)
        exists = (
            db.query(Attendance)
            .filter(and_(Attendance.user_id == user_id, Attendance.attendance_date == check_date))
            .first()
        )
        if exists:
            streak += 1
        else:
            break
    return streak
