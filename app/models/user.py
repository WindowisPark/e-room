from sqlalchemy import Boolean, Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.base import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String, nullable=True)
    full_name = Column(String)
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)  # disabled 대신 is_active 사용
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # OAuth2 관련 필드
    oauth_provider = Column(String, nullable=True)
    oauth_id = Column(String, nullable=True)
    is_verified = Column(Boolean, default=False)

    @property
    def is_admin(self):  # role 기반으로 is_admin 속성 제공
        return self.role == "admin"