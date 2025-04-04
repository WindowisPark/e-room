# app/schemas/team_pdf.py

from pydantic import BaseModel, Field
from datetime import datetime


class PDFMetadata(BaseModel):
    """
    팀 스페이스에서 사용하는 PDF 파일 메타데이터 응답용 모델
    """
    id: int
    filename: str
    file_path: str
    owner_id: int
    owner_username: str
    created_at: datetime

class RenamePDFRequest(BaseModel):
    new_name: str = Field(..., description="변경할 새로운 PDF 파일명 (.pdf 포함)")