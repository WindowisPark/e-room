# app/schemas/notification.py
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class NotificationBase(BaseModel):
    type: str = Field(..., pattern="^(mention|tag|system|team_invitation)$")
    message: str
    link: Optional[str] = None

class NotificationCreate(NotificationBase):
    user_id: int

class NotificationResponse(NotificationBase):
    id: int
    is_read: bool
    created_at: datetime
    
    class Config:
        orm_mode = True