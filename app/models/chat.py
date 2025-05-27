# app/models/chat.py 수정

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from datetime import datetime

class ChatSession(Base):
    """채팅 세션 모델"""
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, default="새 채팅")
    task_type = Column(String, default="qa")
    is_active = Column(Boolean, default=True)
    
    agent_state = Column(JSON, nullable=True)
    waiting_for = Column(String, nullable=True)
    current_request_type = Column(String, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    """채팅 메시지 모델"""
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, ForeignKey("chat_sessions.session_id"))
    message_type = Column(String)  # "user", "ai", "system"
    content = Column(Text)
    
    # ✅ metadata → extra_data로 변경
    extra_data = Column(JSON, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    session = relationship("ChatSession", back_populates="messages")