# app/schemas/collaboration.py

from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class CursorPosition(BaseModel):
    """사용자 커서 위치 정보"""
    user_id: int
    pdf_id: int
    page: int
    x: float = Field(..., ge=0, le=100)  # 페이지 너비 기준 상대 위치 (%)
    y: float = Field(..., ge=0, le=100)  # 페이지 높이 기준 상대 위치 (%)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# 새로운 기본 클래스 추가
class CollaborationMessageBase(BaseModel):
    """협업용 WebSocket 메시지 기본 구조"""
    type: str
    sender_id: int
    sender_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    team_id: int

class CollaborationMessage(CollaborationMessageBase):
    """협업용 WebSocket 메시지 기본 구조"""
    type: str
    sender_id: int
    sender_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    team_id: int
    data: Dict[str, Any]


class CursorUpdateMessage(CollaborationMessage):
    """커서 위치 업데이트 메시지"""
    type: str = "cursor_update"
    data: Dict[str, Any]


class AnnotationCreateMessage(CollaborationMessage):
    """새 주석 생성 메시지"""
    type: str = "annotation_create"
    data: Dict[str, Any]


class AnnotationUpdateMessage(CollaborationMessage):
    """주석 업데이트 메시지"""
    type: str = "annotation_update"
    data: Dict[str, Any]


class AnnotationDeleteMessage(CollaborationMessage):
    """주석 삭제 메시지"""
    type: str = "annotation_delete"
    data: Dict[str, Any]


class UserPresenceMessage(CollaborationMessage):
    """사용자 참여/퇴장 메시지"""
    type: str = "user_presence"
    data: Dict[str, Any]


class TeamActivityLog(BaseModel):
    id: int
    team_id: int
    user_id: int
    username: Optional[str]  # ✅ user.username에서 추출됨
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None
    created_at: datetime

    class Config:
        from_attributes = True  # ✅ Pydantic v2 방식


class TeamActivityLogCreate(BaseModel):
    """팀 활동 로그 생성 요청"""
    team_id: int
    user_id: int
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = None