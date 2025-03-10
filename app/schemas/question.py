from typing import Optional
from datetime import datetime
from pydantic import BaseModel

class QuestionBase(BaseModel):
    """
    질문 기본 스키마
    """
    title: str
    content: str

class QuestionCreate(QuestionBase):
    """
    질문 생성 스키마
    """
    pass

class Question(QuestionBase):
    """
    질문 응답 스키마
    """
    id: int
    user_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True  # Pydantic v2에서는 orm_mode 대신 from_attributes 사용