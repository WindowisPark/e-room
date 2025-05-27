from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime

class ChatSession(Base):
    """채팅 세션 모델 - ChatGPT처럼 대화 세션 관리"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)  # "user_id:uuid" 형태
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, default="새 채팅")  # 자동 생성 또는 사용자 설정
    task_type = Column(String, default="qa")  # qa, summary, exam, schedule
    is_active = Column(Boolean, default=True)
    
    # 세션 상태 정보 (JSON 저장)
    agent_state = Column(JSON, nullable=True)
    waiting_for = Column(String, nullable=True)
    current_request_type = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    """채팅 메시지 모델 - 모든 대화 내용 영구 저장"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("chat_sessions.session_id"))
    
    message_type = Column(String)  # "user", "ai", "system", "file_request", "result"
    content = Column(Text)
    
    # 메타데이터 (JSON 저장)
    metadata = Column(JSON, nullable=True)  # task_type, file_paths, progress 등
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    session = relationship("ChatSession", back_populates="messages")