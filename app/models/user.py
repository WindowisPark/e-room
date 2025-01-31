# ai-agent/app/models/user.py

from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)  # nullable=True로 변경
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)  # OAuth 사용자는 패스워드가 없을 수 있음
    full_name = Column(String)
    role = Column(String, default="user")
    disabled = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # OAuth2 관련 필드
    oauth_provider = Column(String, nullable=True)  # 'google', 'kakao' 등
    oauth_id = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)  # 추가 정보 입력 완료 여부