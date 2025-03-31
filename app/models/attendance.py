# app/models/attendance.py

from sqlalchemy import Column, Integer, Date, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Attendance(Base):
    """
    출석 테이블 모델
    - user_id: 출석한 사용자
    - attendance_date: 출석 일자 (중복 X)
    - created_at: 기록 생성 시간
    """
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    attendance_date = Column(Date, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # ✅ User 관계 설정 추가 (필수!)
    user = relationship("User", back_populates="attendances")
