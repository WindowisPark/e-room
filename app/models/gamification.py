# app/models/gamification.py

from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey, Table, Boolean, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from sqlalchemy import Enum as PgEnum 
from datetime import datetime
from app.db.base_class import Base
import enum

class PointActionType(str, enum.Enum):
    """포인트 적립/차감 액션 타입"""
    ATTENDANCE = "ATTENDANCE"           # 대문자로 맞춤
    ANNOTATION = "ANNOTATION"
    PDF_UPLOAD = "PDF_UPLOAD"
    TEAM_CREATE = "TEAM_CREATE"
    TEAM_JOIN = "TEAM_JOIN"
    LEVEL_UP = "LEVEL_UP"
    ADMIN = "ADMIN"
    EVENT = "EVENT"
    QUEST = "QUEST"
    
    # 🔥 데이터베이스와 일치하도록 추가
    SIGNUP_EVENT = "signup_event"
    INVITE_SENT = "invite_sent"
    INVITE_USED = "invite_used"
    DAILY_LOGIN_EVENT = "daily_login_event"
    SPECIAL_EVENT = "special_event"
    SIGNUP_BONUS = "signup_bonus"        # ✅ 추가
    INVITE_CODE = "invite_code"          # ✅ 추가
    DAILY_LOGIN = "daily_login"          # ✅ 추가
    LEVEL_UP_BONUS = "level_up_bonus"    # ✅ 추가

class BadgeType(str, enum.Enum):
    """배지 타입 구분"""
    ATTENDANCE = "attendance"       # 출석 관련 배지
    ANNOTATION = "annotation"       # 주석 관련 배지
    PDF = "pdf"                     # PDF 관련 배지
    TEAM = "team"                   # 팀 활동 관련 배지
    SPECIAL = "special"             # 특별 배지
    EVENT = "event"                 # 이벤트 배지
    LEVEL = "level"                 # 레벨 관련 배지

class PointHistory(Base):
    """포인트 내역 모델"""
    __tablename__ = "point_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action_type = Column(PgEnum(PointActionType, native_enum=False), nullable=False)
    points = Column(Integer, nullable=False)  # 양수: 적립, 음수: 차감
    description = Column(String(255), nullable=False)
    reference_id = Column(Integer, nullable=True)  # 관련 엔티티 ID (예: 주석 ID)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정
    user = relationship("User", back_populates="point_history")

class Badge(Base):
    """배지 정의 모델"""
    __tablename__ = "badges"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)  # 배지 고유 코드
    name = Column(String(50), nullable=False)
    description = Column(String(255), nullable=False)
    image_url = Column(String(255), nullable=False)  # 배지 이미지 URL
    badge_type = Column(Enum(BadgeType), nullable=False)
    required_level = Column(Integer, nullable=True)  # 획득에 필요한 레벨 (있는 경우)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정
    users = relationship("UserBadge", back_populates="badge")

class UserBadge(Base):
    """사용자-배지 매핑 모델"""
    __tablename__ = "user_badges"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    badge_id = Column(Integer, ForeignKey("badges.id", ondelete="CASCADE"), nullable=False)
    acquired_at = Column(DateTime(timezone=True), server_default=func.now())

    # 관계 설정
    user = relationship("User", back_populates="badges")
    badge = relationship("Badge", back_populates="users")