# app/schemas/event.py

from pydantic import BaseModel, Field
from typing import Dict, Optional
from enum import Enum


class EventType(str, Enum):
    signup_bonus = "signup_bonus"
    invite_code = "invite_code"
    daily_login = "daily_login"
    level_up_bonus = "level_up_bonus"
    special_event = "special_event"


class EventClaimRequest(BaseModel):
    """이벤트 참여 요청"""
    event_type: EventType = Field(..., description="이벤트 타입 (ex: signup_bonus, invite_code)")
    payload: Optional[Dict[str, str]] = Field(default_factory=dict, description="이벤트별 추가 정보")

    class Config:
        schema_extra = {
            "example": {
                "event_type": "invite_code",
                "payload": {
                    "code": "ABC123"
                }
            }
        }


class EventClaimResponse(BaseModel):
    """이벤트 처리 응답"""
    success: bool
    message: Optional[str] = None
    points_awarded: Optional[int] = 0
    bonus_awarded: Optional[int] = 0
