# app/schemas/chat.py 수정

from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class ChatMessageSchema(BaseModel):
    id: int
    type: str
    content: str
    extra_data: Optional[Dict[str, Any]] = None  # ✅ metadata → extra_data
    timestamp: str

class ChatSessionResponse(BaseModel):
    session_id: str
    title: str
    task_type: str
    created_at: str
    updated_at: str
    last_message: str
    message_count: int

class ChatHistoryResponse(BaseModel):
    session_id: str
    title: str
    task_type: str
    created_at: str
    updated_at: str
    messages: List[ChatMessageSchema]
    message_count: int