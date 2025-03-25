# app/schemas/tag.py
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

# 주석 위치 스키마 (페이지 내 좌표)
class PositionData(BaseModel):
    x1: float = Field(..., ge=0, le=100)  # 좌측 상단 X좌표 (페이지 너비의 백분율)
    y1: float = Field(..., ge=0, le=100)  # 좌측 상단 Y좌표 (페이지 높이의 백분율)
    x2: float = Field(..., ge=0, le=100)  # 우측 하단 X좌표 (페이지 너비의 백분율)
    y2: float = Field(..., ge=0, le=100)  # 우측 하단 Y좌표 (페이지 높이의 백분율)

# 주석 생성 스키마
class AnnotationBase(BaseModel):
    pdf_id: int
    page: int = Field(..., ge=1)  # 페이지 번호는 1부터 시작
    content: str
    position: Dict[str, float]  # JSON으로 저장되는 위치 데이터
    annotation_type: str = Field("highlight", pattern="^(highlight|note|underline|drawing)$")

class AnnotationCreate(AnnotationBase):
    pass

class AnnotationUpdate(BaseModel):
    content: Optional[str] = None
    position: Optional[Dict[str, float]] = None

# 주석 응답 스키마
class AnnotationResponse(AnnotationBase):
    id: int
    user_id: int
    username: str
    created_at: datetime
    mentions: List[str] = []
    hashtags: List[str] = []
    
    class Config:
        orm_mode = True

# 주석 목록 응답 스키마
class AnnotationList(BaseModel):
    pdf_id: int
    file_name: str
    page: Optional[int] = None
    annotations: List[AnnotationResponse]
    
    class Config:
        orm_mode = True