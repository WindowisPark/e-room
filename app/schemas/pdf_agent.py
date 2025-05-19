# app/schemas/pdf_agent.py

from pydantic import BaseModel, Field
from typing import List, Optional


class SummaryRequest(BaseModel):
    folder: str = Field(..., description="사용자 폴더 이름 또는 문서 키")
    level: Optional[str] = Field("default", description="요약 수준: default, short, detailed")


class SummaryResponse(BaseModel):
    success: bool
    summary: str
    message: Optional[str] = None


class QARequest(BaseModel):
    folder: str
    query: str


class QAResponse(BaseModel):
    success: bool
    answer: str
    query: str
    message: Optional[str] = None


class QuestionGenerationRequest(BaseModel):
    folder: str
    count: Optional[int] = Field(5, ge=1, le=20)


class QuestionGenerationResponse(BaseModel):
    success: bool
    questions: str
    count: int
    message: Optional[str] = None
