# app/models/user.py

from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.models.question import Question

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    full_name = Column(String)
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 📱 전화번호 필드
    phone_number = Column(String, nullable=True)
    is_phone_verified = Column(Boolean, default=False)

    # ✅ 멘션 알림 수신 여부 설정 (feat)
    allow_mention_notifications = Column(Boolean, default=True)

    # 📅 출석
    attendances = relationship("Attendance", back_populates="user", cascade="all, delete-orphan")

    # 🔐 OAuth2
    oauth_provider = Column(String, nullable=True)
    oauth_id = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)

    # 👥 팀
    owned_teams = relationship("Team", back_populates="owner", foreign_keys="Team.owner_id")
    team_memberships = relationship("TeamMember", back_populates="user")

    # 📄 PDF
    pdf_files = relationship("PDFFile", back_populates="owner")
    pdf_tags = relationship("PDFTag", back_populates="user")
    pdf_mentions = relationship("PDFTagMention", back_populates="user")

    # 🔔 알림
    notifications = relationship("Notification", back_populates="user")

    # ❓ 질문
    questions = relationship("Question", back_populates="user", cascade="all, delete-orphan")

    # 💳 결제
    payments = relationship("Payment", back_populates="user")

    @property
    def is_admin(self):
        return self.role == "admin"
    
    # 🔥 팀 활동 로그 (역참조)
    team_activities = relationship(
        "TeamActivity",
        back_populates="user",
        cascade="all, delete-orphan"
    )
