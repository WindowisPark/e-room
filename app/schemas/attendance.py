# app/schemas/attendance.py

from datetime import datetime, date
from pydantic import BaseModel

class AttendanceBase(BaseModel):
    user_id: int
    attendance_date: date

class AttendanceCreate(AttendanceBase):
    pass

class Attendance(AttendanceBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True  # SQLAlchemy 모델과 호환 가능하도록 설정

class AttendanceResponse(BaseModel):
    """
    출석 요청에 대한 응답 구조
    - success: 출석 성공 여부
    - message: 사용자 피드백 메시지
    - current_streak: 현재 연속 출석 일수
    - today_checked: 오늘 이미 출석했는지 여부
    - today: 오늘 날짜
    """
    success: bool
    message: str
    current_streak: int
    today_checked: bool
    today: date
