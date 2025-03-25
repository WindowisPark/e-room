# app/models/notification.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Notification(Base):
    """
    사용자 알림 모델
    """
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    type = Column(String(20), nullable=False)  # mention, tag, system 등 알림 타입
    message = Column(Text, nullable=False)  # 알림 메시지
    link = Column(Text, nullable=True)  # 알림 클릭 시 이동할 링크
    is_read = Column(Boolean, default=False)  # 읽음 여부
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    user = relationship("User", back_populates="notifications")