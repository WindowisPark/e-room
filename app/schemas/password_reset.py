# app/schemas/password_reset.py

from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional
from datetime import datetime

class PasswordResetRequest(BaseModel):
    """비밀번호 재설정 요청 스키마"""
    email: EmailStr = Field(
        ..., 
        description="등록된 이메일 주소",
        example="user@example.com"
    )

class PasswordResetResponse(BaseModel):
    """비밀번호 재설정 요청 응답 스키마"""
    message: str = Field(..., description="응답 메시지")
    email: str = Field(..., description="요청한 이메일 주소")
    token_expires_in_minutes: Optional[int] = Field(
        None, 
        description="토큰 만료 시간(분)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "message": "비밀번호 재설정 링크를 이메일로 발송했습니다.",
                "email": "user@example.com",
                "token_expires_in_minutes": 30
            }
        }

class PasswordResetConfirm(BaseModel):
    """비밀번호 재설정 확인 스키마"""
    token: str = Field(
        ..., 
        min_length=32,
        max_length=255,
        description="재설정 토큰"
    )
    new_password: str = Field(
        ..., 
        min_length=8,
        max_length=128,
        description="새 비밀번호"
    )
    confirm_password: str = Field(
        ..., 
        min_length=8,
        max_length=128,
        description="비밀번호 확인"
    )

    @validator('new_password')
    def validate_password_strength(cls, v):
        """비밀번호 강도 검증"""
        if len(v) < 8:
            raise ValueError('비밀번호는 최소 8자 이상이어야 합니다')
        
        # 영문, 숫자, 특수문자 중 2종류 이상 포함 권장
        has_alpha = any(c.isalpha() for c in v)
        has_digit = any(c.isdigit() for c in v)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in v)
        
        criteria_met = sum([has_alpha, has_digit, has_special])
        if criteria_met < 2:
            raise ValueError('비밀번호는 영문, 숫자, 특수문자 중 2종류 이상을 포함해야 합니다')
        
        return v

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        """비밀번호 일치 검증"""
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('비밀번호가 일치하지 않습니다')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "token": "abc123def456ghi789jkl012mno345pqr678stu901vwx234yzabc567def890ghi",
                "new_password": "newPassword123!",
                "confirm_password": "newPassword123!"
            }
        }

class PasswordResetConfirmResponse(BaseModel):
    """비밀번호 재설정 완료 응답 스키마"""
    message: str = Field(..., description="완료 메시지")
    success: bool = Field(..., description="성공 여부")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "비밀번호가 성공적으로 변경되었습니다.",
                "success": True
            }
        }

class TokenValidationRequest(BaseModel):
    """토큰 유효성 검사 요청 스키마"""
    token: str = Field(
        ..., 
        min_length=32,
        max_length=255,
        description="검증할 재설정 토큰"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "token": "abc123def456ghi789jkl012mno345pqr678stu901vwx234yzabc567def890ghi"
            }
        }

class TokenValidationResponse(BaseModel):
    """토큰 유효성 검사 응답 스키마"""
    valid: bool = Field(..., description="토큰 유효성")
    message: str = Field(..., description="검증 결과 메시지")
    expires_at: Optional[datetime] = Field(
        None, 
        description="토큰 만료 시간 (유효한 경우)"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "valid": True,
                "message": "유효한 토큰입니다.",
                "expires_at": "2024-01-15T10:30:00"
            }
        }

# OAuth 사용자용 응답 스키마
class OAuthUserResetResponse(BaseModel):
    """OAuth 사용자 비밀번호 재설정 응답"""
    message: str = Field(..., description="OAuth 안내 메시지")
    oauth_provider: str = Field(..., description="OAuth 제공자")
    redirect_url: Optional[str] = Field(None, description="OAuth 비밀번호 변경 URL")
    
    class Config:
        schema_extra = {
            "example": {
                "message": "카카오 계정입니다. 카카오에서 비밀번호를 재설정해 주세요.",
                "oauth_provider": "kakao",
                "redirect_url": "https://accounts.kakao.com/password"
            }
        }