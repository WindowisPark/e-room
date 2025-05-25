# app/models/event.py

from datetime import datetime
import enum
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

class EventType(str, enum.Enum):
    """이벤트 타입 정의"""
    SIGNUP_BONUS = "signup_bonus"           # 신규가입 보너스
    INVITE_CODE = "invite_code"             # 친구 초대 이벤트
    DAILY_LOGIN = "daily_login"             # 일일 로그인 보너스 (향후 확장)
    LEVEL_UP_BONUS = "level_up_bonus"       # 레벨업 보너스 (향후 확장)
    SPECIAL_EVENT = "special_event"         # 특별 이벤트 (향후 확장)

class EventStatus(str, enum.Enum):
    """이벤트 상태"""
    ACTIVE = "active"       # 활성화
    INACTIVE = "inactive"   # 비활성화
    ENDED = "ended"         # 종료됨
    SCHEDULED = "scheduled" # 예정됨

class Event(Base):
    """
    이벤트 정의 모델
    - 이벤트의 기본 정보와 조건을 관리
    """
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, comment="이벤트 이름")
    event_type = Column(Enum(EventType), nullable=False, index=True, comment="이벤트 타입")
    description = Column(Text, nullable=True, comment="이벤트 설명")
    
    # 이벤트 기간
    start_date = Column(DateTime, nullable=True, comment="이벤트 시작일")
    end_date = Column(DateTime, nullable=True, comment="이벤트 종료일")
    
    # 이벤트 상태 및 설정
    status = Column(Enum(EventStatus), default=EventStatus.ACTIVE, nullable=False, comment="이벤트 상태")
    is_repeatable = Column(Boolean, default=False, comment="반복 참여 가능 여부")
    max_participants = Column(Integer, nullable=True, comment="최대 참여자 수 (제한 없으면 NULL)")
    
    # 보상 설정
    reward_points = Column(Integer, default=0, comment="기본 지급 포인트")
    bonus_points = Column(Integer, default=0, comment="보너스 포인트")
    
    # 이벤트 조건 (JSON으로 유연하게 관리)
    conditions = Column(JSON, nullable=True, comment="이벤트 참여 조건 (JSON)")
    
    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True, comment="이벤트 생성자 (관리자)")

    # 관계 설정
    user_events = relationship("UserEvent", back_populates="event", cascade="all, delete-orphan")
    invite_codes = relationship("InviteCode", back_populates="event", cascade="all, delete-orphan")

    @property
    def is_active(self) -> bool:
        """이벤트가 현재 활성화 상태인지 확인"""
        if self.status != EventStatus.ACTIVE:
            return False
        
        now = datetime.utcnow()
        
        # 시작일 체크
        if self.start_date and self.start_date > now:
            return False
            
        # 종료일 체크
        if self.end_date and self.end_date < now:
            return False
            
        return True

    @property
    def current_participants(self) -> int:
        """현재 참여자 수"""
        return len([ue for ue in self.user_events if ue.is_completed])

class UserEvent(Base):
    """
    사용자별 이벤트 참여 이력
    - 중복 참여 방지 및 참여 이력 관리
    """
    __tablename__ = "user_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 참여 상태
    is_completed = Column(Boolean, default=False, comment="이벤트 완료 여부")
    completion_date = Column(DateTime, nullable=True, comment="완료 일시")
    
    # 보상 정보
    points_earned = Column(Integer, default=0, comment="획득한 포인트")
    bonus_earned = Column(Integer, default=0, comment="획득한 보너스 포인트")
    
    # 이벤트별 추가 데이터 (JSON으로 유연하게 관리)
    event_data = Column(JSON, nullable=True, comment="이벤트별 추가 데이터")
    
    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 관계 설정
    user = relationship("User", back_populates="user_events")
    event = relationship("Event", back_populates="user_events")

    # 복합 유니크 제약조건 (사용자당 이벤트별 1회 제한, 반복 가능한 이벤트 제외)
    __table_args__ = (
        # Index for performance
        {"comment": "사용자별 이벤트 참여 이력"}
    )

    def mark_completed(self, points: int = 0, bonus: int = 0, data: dict = None):
        """이벤트 완료 처리"""
        self.is_completed = True
        self.completion_date = datetime.utcnow()
        self.points_earned = points
        self.bonus_earned = bonus
        if data:
            self.event_data = data

class InviteCode(Base):
    """
    초대 코드 관리 모델
    - 친구 초대 이벤트에서 사용되는 초대 코드
    """
    __tablename__ = "invite_codes"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, nullable=False, index=True, comment="초대 코드")
    
    # 코드 소유자 및 이벤트
    inviter_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # 사용 정보
    is_used = Column(Boolean, default=False, comment="사용 여부")
    used_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="사용한 사용자")
    used_at = Column(DateTime, nullable=True, comment="사용 일시")
    
    # 코드 설정
    expires_at = Column(DateTime, nullable=True, comment="만료 일시")
    max_uses = Column(Integer, default=1, comment="최대 사용 횟수")
    current_uses = Column(Integer, default=0, comment="현재 사용 횟수")
    
    # 메타데이터
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 관계 설정
    inviter = relationship("User", foreign_keys=[inviter_id], back_populates="generated_invite_codes")
    used_by = relationship("User", foreign_keys=[used_by_id], back_populates="used_invite_codes")
    event = relationship("Event", back_populates="invite_codes")

    @property
    def is_valid(self) -> bool:
        """초대 코드가 유효한지 확인"""
        # 사용 횟수 체크
        if self.current_uses >= self.max_uses:
            return False
            
        # 만료일 체크
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
            
        return True

    def use_code(self, user_id: int) -> bool:
        """초대 코드 사용 처리"""
        if not self.is_valid:
            return False
            
        self.current_uses += 1
        self.used_by_id = user_id
        self.used_at = datetime.utcnow()
        
        # 1회용 코드인 경우 사용됨으로 표시
        if self.max_uses == 1:
            self.is_used = True
            
        return True