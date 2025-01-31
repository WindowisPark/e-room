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