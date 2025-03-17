# app/core/config.py
    
import os
from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # 프로젝트 기본 설정
    PROJECT_NAME: str = "AI-Agent API"
    API_V1_STR: str = "/api/v1"
    
    # ✅ PostgreSQL 설정
    POSTGRES_SERVER: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    DATABASE_URI: Optional[str] = None

    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-default-secret-key")
    
    # ✅ JWT 관련 설정 (Access / Refresh Token 분리)
    ACCESS_SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int

    # Redis 캐시 관련 설정
    REDIS_CACHE_HOST: str = "redis"
    REDIS_CACHE_PORT: int = 6379
    REDIS_CACHE_DB: int = 1
    FILE_LIST_CACHE_TTL: int = 300
    FOLDER_LIST_CACHE_TTL: int = 300
    
    # Redis 접속 설정 (기존 redis_helper.py와 호환성 유지)
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # ✅ Kakao OAuth2 설정
    KAKAO_CLIENT_ID: str
    KAKAO_CLIENT_SECRET: str
    KAKAO_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/kakao/callback"

    # ✅ CORS 설정
    BACKEND_CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:8000"]

    # ✅ OAuth Refresh Token 만료일
    OAUTH_REFRESH_TOKEN_EXPIRE_DAYS: int
    
    # ✅ iamport Webhook 관련 설정
    IAMPORT_WEBHOOK_SECRET: str = ""
    
    # ✅ SMS 인증 관련 설정 (필요한 경우 추가)
    SMS_API_KEY: Optional[str] = None
    SMS_API_SECRET: Optional[str] = None
    SMS_SENDER_NUMBER: Optional[str] = None
    
    # Pydantic v2 설정
    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "allow"  # 추가 필드 허용
    }

    # ✅ DB 연결 문자열 자동 생성 (Pydantic v2 방식)
    @model_validator(mode='before')
    def assemble_db_connection(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if isinstance(values, dict):
            if values.get('DATABASE_URI') is None:
                postgres_user = values.get('POSTGRES_USER')
                postgres_password = values.get('POSTGRES_PASSWORD')
                postgres_server = values.get('POSTGRES_SERVER')
                postgres_db = values.get('POSTGRES_DB')
                
                if all([postgres_user, postgres_password, postgres_server, postgres_db]):
                    values['DATABASE_URI'] = f"postgresql://{postgres_user}:{postgres_password}@{postgres_server}/{postgres_db}"
        return values

    # ✅ CORS 설정 검증 (Pydantic v2 방식)
    @field_validator("BACKEND_CORS_ORIGINS", mode='before')
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # ✅ 환경 변수에서 숫자 값이 문자열로 인식되는 문제 해결 (Pydantic v2 방식)
    @field_validator("ACCESS_TOKEN_EXPIRE_MINUTES", "REFRESH_TOKEN_EXPIRE_DAYS", "OAUTH_REFRESH_TOKEN_EXPIRE_DAYS", "REDIS_PORT", "REDIS_DB", "REDIS_CACHE_PORT", "REDIS_CACHE_DB", "FILE_LIST_CACHE_TTL", "FOLDER_LIST_CACHE_TTL", mode='before')
    @classmethod
    def parse_int_values(cls, v: Union[str, int]) -> int:
        return int(v) if isinstance(v, str) else v

settings = Settings()

# ✅ 환경 변수 확인 (테스트용)
print(f"Loaded API_V1_STR: {settings.API_V1_STR}")
print(f"Loaded DATABASE_URI: {settings.DATABASE_URI}")
print(f"Loaded CORS Origins: {settings.BACKEND_CORS_ORIGINS}")
print(f"Loaded Redis Host: {settings.REDIS_HOST}")
print(f"Loaded Redis Port: {settings.REDIS_PORT}")
print(f"Loaded Access Token Expiry: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
print(f"Loaded Refresh Token Expiry: {settings.REFRESH_TOKEN_EXPIRE_DAYS}")