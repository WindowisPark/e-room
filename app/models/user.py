# app/models/user.py

from datetime import datetime
import enum
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from app.models.question import Question

class PlanType(str, enum.Enum):
    free = "free"
    premium = "premium"
    vip = "vip"



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

    # 게이미피케이션을 위한 필드 추가
    points = Column(Integer, default=0)  # 누적 포인트
    level = Column(Integer, default=1)   # 사용자 레벨
    exp = Column(Integer, default=0)     # 경험치
    streak_days = Column(Integer, default=0)  # 연속 출석일

    point_history = relationship("PointHistory", back_populates="user", cascade="all, delete-orphan")
    badges = relationship("UserBadge", back_populates="user", cascade="all, delete-orphan")

    @property
    def is_admin(self):
        return self.role == "admin"

    # 🔥 팀 활동 로그 (역참조)
    team_activities = relationship(
        "TeamActivity",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # User 클래스 내부에 추가
    plan_type = Column(Enum(PlanType), default=PlanType.free, nullable=False)
    plan_started_at = Column(DateTime, nullable=True)
    plan_expires_at = Column(DateTime, nullable=True)

    @property
    def max_team_spaces(self):
        """현재 요금제에 따른 최대 팀스페이스 수 반환"""
        # 요금제 만료 확인
        if self.plan_expires_at and self.plan_expires_at < datetime.now():
            return 0  # 만료된 경우 free 플랜과 동일하게 처리

        if self.plan_type == PlanType.premium:
            return 1
        elif self.plan_type == PlanType.vip:
            return 5
        return 0  # free 플랜

    @property
    def is_plan_active(self):
        """현재 요금제가 활성 상태인지 확인"""
        if not self.plan_expires_at:
            return self.plan_type != PlanType.free
        return self.plan_expires_at > datetime.now()

    @property
    def days_until_expiry(self):
        """요금제 만료까지 남은 일수"""
        if not self.plan_expires_at:
            return 0
        delta = self.plan_expires_at - datetime.now()
        return max(0, delta.days)
