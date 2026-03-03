# app/models/cover_letter.py

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base_class import Base


class CoverLetter(Base):
    __tablename__ = "cover_letters"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    company_id = Column(Integer, ForeignKey("saved_companies.id", ondelete="SET NULL"), nullable=True)
    resume_profile_id = Column(Integer, ForeignKey("resume_profiles.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(300), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    items = relationship("CoverLetterItem", back_populates="cover_letter", cascade="all, delete-orphan", order_by="CoverLetterItem.order_index")


class CoverLetterItem(Base):
    __tablename__ = "cover_letter_items"

    id = Column(Integer, primary_key=True, index=True)
    cover_letter_id = Column(Integer, ForeignKey("cover_letters.id", ondelete="CASCADE"), nullable=False, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=True)
    char_limit = Column(Integer, nullable=True)    # 글자수 제한 (0 = 제한 없음)
    order_index = Column(Integer, default=0)

    cover_letter = relationship("CoverLetter", back_populates="items")
