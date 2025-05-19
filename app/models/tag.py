#app/models/tag.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from app.models.team import Team
    from app.models.user import User

class PDFFile(Base):
    """
    PDF 파일 모델
    """
    __tablename__ = "pdf_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    team = relationship("Team", back_populates="pdf_files")
    owner = relationship("User", back_populates="pdf_files")
    tags = relationship("PDFTag", back_populates="pdf_file", cascade="all, delete-orphan")

class PDFTag(Base):
    """
    PDF 태그/주석 모델
    """
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    pdf_id = Column(Integer, ForeignKey("pdf_files.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id"))
    page = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    position = Column(JSON)  # 페이지 내 좌표 (x1,y1,x2,y2) 백분율로 저장
    annotation_type = Column(String(20), default="highlight")  # highlight, note, underline 등
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    pdf_file = relationship("PDFFile", back_populates="tags")
    user = relationship("User", back_populates="pdf_tags")
    mentions = relationship("PDFTagMention", back_populates="tag", cascade="all, delete-orphan")

class PDFTagMention(Base):
    """
    PDF 태그 내 멘션 모델
    """
    __tablename__ = "mentions"
    
    id = Column(Integer, primary_key=True, index=True)
    tag_id = Column(Integer, ForeignKey("tags.id", ondelete="CASCADE"))
    mentioned_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    notification_sent = Column(Boolean, default=False)
    
    # 관계 설정
    tag = relationship("PDFTag", back_populates="mentions")
    user = relationship("User", back_populates="pdf_mentions")