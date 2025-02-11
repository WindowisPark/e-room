# app/core/config.py
    
import os
from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, validator
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

    # ✅ Redis 설정 (Refresh Token 저장용)
    REDIS_HOST: str
    REDIS_PORT: int
    REDIS_DB: int

    # ✅ OAuth2 설정 (Google, Naver, Kakao)
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/google/callback"

    NAVER_CLIENT_ID: str
    NAVER_CLIENT_SECRET: str
    NAVER_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/naver/callback"

    KAKAO_CLIENT_ID: str
    KAKAO_CLIENT_SECRET: str
    KAKAO_REDIRECT_URI: str = "http://localhost:8000/api/v1/auth/kakao/callback"

    # ✅ CORS 설정
    BACKEND_CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:8000"]

    # ✅ OAuth Refresh Token 만료일 추가
    OAUTH_REFRESH_TOKEN_EXPIRE_DAYS: int

    # ✅ DB 연결 문자열 자동 생성
    @validator("DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        return f"postgresql://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}/{values.get('POSTGRES_DB')}"

    # ✅ CORS 설정 검증
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # ✅ 환경 변수에서 숫자 값이 문자열로 인식되는 문제 해결
    @validator("ACCESS_TOKEN_EXPIRE_MINUTES", "REFRESH_TOKEN_EXPIRE_DAYS", "OAUTH_REFRESH_TOKEN_EXPIRE_DAYS", "REDIS_PORT", "REDIS_DB", pre=True)
    def parse_int_values(cls, v: Union[str, int]) -> int:
        return int(v) if isinstance(v, str) else v

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()

# ✅ 환경 변수 확인 (테스트용)
print(f"Loaded API_V1_STR: {settings.API_V1_STR}")
print(f"Loaded DATABASE_URI: {settings.DATABASE_URI}")
print(f"Loaded CORS Origins: {settings.BACKEND_CORS_ORIGINS}")
print(f"Loaded Redis Host: {settings.REDIS_HOST}")
print(f"Loaded Redis Port: {settings.REDIS_PORT}")
print(f"Loaded Access Token Expiry: {settings.ACCESS_TOKEN_EXPIRE_MINUTES}")
print(f"Loaded Refresh Token Expiry: {settings.REFRESH_TOKEN_EXPIRE_DAYS}")