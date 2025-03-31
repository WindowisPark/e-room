# app/crud/crud_attendance.py

from datetime import date, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.attendance import Attendance

class CRUDAttendance:
    def upsert_attendance(self, db: Session, user_id: int) -> Attendance:
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

    def get_current_streak(self, db: Session, user_id: int, limit: int = 7) -> int:
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

# 객체 인스턴스화
crud_attendance = CRUDAttendance()
