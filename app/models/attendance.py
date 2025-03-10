# app/models/attendance.py
from sqlalchemy import Column, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class Attendance(Base):
    __tablename__ = "attendances"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    attendance_date = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

    # 관계 설정 (user 테이블과 연결)
    user = relationship("User", back_populates="attendances")