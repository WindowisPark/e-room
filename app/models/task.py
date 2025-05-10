from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base_class import Base

class Task(Base):
    __tablename__ = "tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    task_type = Column(String, nullable=False)  # summarize, generate_questions, answer_question
    document_id = Column(Integer, ForeignKey("pdf_files.id"), nullable=False)
    status = Column(String, default="pending")  # pending, processing, completed, failed
    progress = Column(Float, default=0)  # 0-100
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 관계 설정
    user = relationship("User", back_populates="tasks")
    document = relationship("PDFFile", back_populates="tasks")
    