# ai-agent/app/schemas/user.py

from typing import Optional, Dict, List, Any
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserBase(BaseModel):
    email: Optional[EmailStr] = None 
    username: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = False

class UserCreate(UserBase):
    email: EmailStr
    password: str

class UserCreateOAuth(BaseModel):
    oauth_provider: str
    oauth_id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    username: Optional[str] = None
    phone_number: Optional[str] = None  # 전화번호 필드 추가
    is_verified: bool = False

    class Config:
        from_attributes = True

class UserUpdate(UserBase):
    password: Optional[str] = None

class UserInDBBase(UserBase):
    id: int
    email: Optional[EmailStr] = None  # <- Optional로 변경
    role: str
    created_at: datetime

    class Config:
        from_attributes = True

class User(UserInDBBase):
    pass

class UserInDB(UserInDBBase):
    hashed_password: Optional[str] = None

class UserProfileUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None

    class Config:
        from_attributes = True

class UserResponse(BaseModel):
    """📌 사용자 응답 모델"""
    id: int
    email: Optional[str]  # email이 nullable하므로 Optional로 변경
    username: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
    oauth_provider: Optional[str]
    oauth_id: Optional[str]
    is_verified: bool
    is_admin: bool  # 이미 User 모델에 @property로 정의되어 있음

    class Config:
        from_attributes = True

# app/schemas/user.py 스키마 업데이트
class UserDetailResponse(BaseModel):
    """사용자 상세 정보 응답 모델"""
    user: Dict[str, Any]
    signup_info: Dict[str, Any]  # 가입 정보 추가
    subscription: Dict[str, Any]
    payment: Optional[Dict[str, Any]] = None
    storage: Dict[str, Any]
    teams: List[Dict[str, Any]]
    gamification: Dict[str, Any]
    activity: Dict[str, Any]
    notifications: Dict[str, Any]
    recent_badges: List[Dict[str, Any]]
    
    class Config:
        from_attributes = True

class ErrorResponse(BaseModel):
    """📌 오류 응답 모델"""
    detail: str