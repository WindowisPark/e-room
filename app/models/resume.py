# app/models/resume.py

import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class ItemCategory(str, enum.Enum):
    experience = "experience"
    project = "project"
    cert = "cert"
    activity = "activity"
    skill = "skill"
    education = "education"


class ResumeProfile(Base):
    __tablename__ = "resume_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    summary = Column(Text, nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    items = relationship("ResumeItem", back_populates="profile", cascade="all, delete-orphan", order_by="ResumeItem.order_index")


class ResumeItem(Base):
    __tablename__ = "resume_items"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, ForeignKey("resume_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(SAEnum(ItemCategory), nullable=False)
    title = Column(String(300), nullable=False)
    organization = Column(String(300), nullable=True)
    start_date = Column(String(20), nullable=True)   # "2023-03" 형식
    end_date = Column(String(20), nullable=True)     # "2024-06" 또는 "현재"
    description = Column(Text, nullable=True)
    tags = Column(JSON, nullable=True)               # ["Python", "FastAPI"]
    order_index = Column(Integer, default=0)

    profile = relationship("ResumeProfile", back_populates="items")
