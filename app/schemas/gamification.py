# app/schemas/gamification.py

from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

# Point-related schemas
class PointActionType(str, Enum):
    ATTENDANCE = "attendance"
    ANNOTATION = "annotation"
    PDF_UPLOAD = "pdf_upload"
    TEAM_CREATE = "team_create"
    TEAM_JOIN = "team_join"
    LEVEL_UP = "level_up"
    ADMIN = "admin"
    EVENT = "event"
    QUEST = "quest"

    # ✅ 새로운 값 추가
    SIGNUP_BONUS = "signup_bonus"  # ✅ EventType과 일치시킴
    INVITE_CODE = "invite_code"
    DAILY_LOGIN = "daily_login"
    LEVEL_UP_BONUS = "level_up_bonus"
    SPECIAL_EVENT = "special_event"

class PointHistoryBase(BaseModel):
    action_type: PointActionType
    points: int
    description: str
    reference_id: Optional[int] = None

class PointHistoryCreate(PointHistoryBase):
    user_id: int

class PointHistoryResponse(PointHistoryBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class PointSummary(BaseModel):
    total_points: int
    current_level: int
    points_to_next_level: int
    level_progress_percent: float
    streak_days: int

# Badge-related schemas
class BadgeType(str, Enum):
    ATTENDANCE = "attendance"
    ANNOTATION = "annotation"
    PDF = "pdf"
    TEAM = "team"
    SPECIAL = "special"
    EVENT = "event"
    LEVEL = "level"

class BadgeBase(BaseModel):
    code: str
    name: str
    description: str
    image_url: str
    badge_type: BadgeType
    required_level: Optional[int] = None

class BadgeCreate(BadgeBase):
    pass

class BadgeResponse(BadgeBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

class UserBadgeResponse(BaseModel):
    id: int
    badge: BadgeResponse
    acquired_at: datetime

    class Config:
        from_attributes = True

# Level-related schemas
class LevelInfo(BaseModel):
    level: int
    min_points: int
    max_points: int
    points_to_next_level: int

class UserLevelInfoResponse(BaseModel):
    current_level: int
    current_points: int
    next_level_points: int
    progress_percent: float

class UserGamificationProfile(BaseModel):
    user_id: int
    username: str
    points: int
    level: int
    level_progress: float
    streak_days: int
    badges_count: int
    recent_badges: List[UserBadgeResponse]

    class Config:
        from_attributes = True