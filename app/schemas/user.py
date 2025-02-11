# ai-agent/app/schemas/user.py

from typing import Optional
from pydantic import BaseModel, EmailStr
from datetime import datetime

class UserBase(BaseModel):
    email: Optional[EmailStr] = Optional
    username: Optional[str] = None
    full_name: Optional[str] = None
    disabled: Optional[bool] = False

class UserCreate(UserBase):
    email: EmailStr
    password: str

class UserCreateOAuth(BaseModel):
    oauth_provider: str
    oauth_id: str
    email: Optional[str] = None  # EmailStr에서 str로 변경하고 Optional로
    full_name: Optional[str] = None
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

class ErrorResponse(BaseModel):
    """📌 오류 응답 모델"""
    detail: str