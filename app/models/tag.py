# app/models/tag.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class PDFFile(Base):
    """
    PDF 파일 모델
    """
    __tablename__ = "pdf_files"
    
    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)  # 실제 파일 경로 또는 S3 URL
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)  # 팀스페이스에 속할 수도 있고, 개인 파일일 수도 있음
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