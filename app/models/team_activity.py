# app/models/team_activity.py

from sqlalchemy.orm import relationship
from app.db.base_class import Base  # 상속하는 Base
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from datetime import datetime

class TeamActivity(Base):
    """
    팀 활동 로그 모델
    - 주석 생성/수정/삭제, 파일 업로드/삭제 등 활동을 기록
    """
    __tablename__ = "team_activities"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(Integer, nullable=True)
    details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # 🔄 역참조는 back_populates로 명시적으로 연결
    user = relationship("User", back_populates="team_activities")
    team = relationship("Team", back_populates="activities")

    @property
    def username(self) -> str:
        return self.user.username if self.user else None