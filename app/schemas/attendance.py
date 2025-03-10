# app/schemas/attendance.py

from datetime import datetime
from pydantic import BaseModel
from typing import Optional

class AttendanceBase(BaseModel):
    user_id: int
    attendance_date: datetime

class AttendanceCreate(AttendanceBase):
    pass

class Attendance(AttendanceBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True