# app/models/job_research.py

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func

from app.db.base_class import Base


class SavedCompany(Base):
    __tablename__ = "saved_companies"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_name = Column(String(200), nullable=False)
    job_title = Column(String(300), nullable=True)
    source_url = Column(String(1000), nullable=True)
    raw_content = Column(Text, nullable=True)   # 원문 공고 텍스트
    analysis = Column(JSON, nullable=True)       # AI 분석 결과
    created_at = Column(DateTime(timezone=True), server_default=func.now())
