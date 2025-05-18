# app/schemas/local_auth.py
from typing import Optional
from pydantic import BaseModel, EmailStr, validator

class LocalUserCreate(BaseModel):
    """자체 회원가입 요청 스키마"""
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    
    @validator('username')
    def username_alphanumeric(cls, v):
        if not v.isalnum():
            raise ValueError('사용자명은 알파벳과 숫자만 허용합니다')
        return v
    
    @validator('password')
    def password_min_length(cls, v):
        if len(v) < 8:
            raise ValueError('비밀번호는 최소 8자 이상이어야 합니다')
        return v

class LocalUserLogin(BaseModel):
    """자체 로그인 요청 스키마"""
    email: EmailStr
    password: str

class Token(BaseModel):
    """토큰 응답 스키마"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: int
    username: str
    email: str
    is_admin: bool

class RegisterResponse(BaseModel):
    """회원가입 응답 스키마"""
    user_id: int
    email: str
    username: str
    message: str = "회원가입이 완료되었습니다"