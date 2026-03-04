# app/models/tag.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.db.base_class import Base


class PDFFile(Base):
    __tablename__ = "pdf_files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(255), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="pdf_files")
    tags = relationship("PDFTag", back_populates="pdf_file", cascade="all, delete-orphan")


class PDFTag(Base):
    __tablename__ = "tags"

    id = Column(Integer, primary_key=True, index=True)
    pdf_id = Column(Integer, ForeignKey("pdf_files.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id"))
    page = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    position = Column(JSON)
    annotation_type = Column(String(20), default="highlight")
    created_at = Column(DateTime, default=datetime.utcnow)

    pdf_file = relationship("PDFFile", back_populates="tags")
    user = relationship("User", back_populates="pdf_tags")
