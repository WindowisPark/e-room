# app/models/password_reset.py

from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from datetime import datetime
from app.db.base_class import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

class PasswordResetToken(Base):
    """
    비밀번호 재설정 토큰 모델
    
    사용자가 비밀번호 찾기를 요청했을 때 생성되는 일회성 토큰을 관리합니다.
    보안을 위해 토큰은 30분간만 유효하며, 사용 후 즉시 무효화됩니다.
    """
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    token = Column(String(255), unique=True, index=True, nullable=False)
    is_used = Column(Boolean, default=False, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    used_at = Column(DateTime, nullable=True)

    # 관계 설정
    user = relationship("User", back_populates="password_reset_tokens")

    @property
    def is_expired(self) -> bool:
        """토큰 만료 여부 확인"""
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """
        토큰 유효성 확인
        - 만료되지 않았고
        - 아직 사용되지 않은 경우에만 유효
        """
        return not self.is_expired and not self.is_used

    def mark_as_used(self) -> None:
        """토큰을 사용 완료로 표시"""
        self.is_used = True
        self.used_at = datetime.utcnow()

    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, is_valid={self.is_valid})>"