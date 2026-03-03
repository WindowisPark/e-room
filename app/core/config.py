import os
from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "AI-Agent API"
    API_V1_STR: str = "/api/v1"

    # PostgreSQL — 개별 항목 또는 DATABASE_URL(Railway) 둘 다 지원
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str = "agent_db"
    DATABASE_URI: Optional[str] = None
    DATABASE_URL: Optional[str] = None  # Railway PostgreSQL 공개 URL
    DATABASE_PRIVATE_URL: Optional[str] = None  # Railway 내부망 URL (egress 없음)

    # JWT
    SECRET_KEY: str
    ACCESS_SECRET_KEY: str
    REFRESH_SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Redis — REDIS_PRIVATE_URL(Railway 내부망) 우선, 없으면 REDIS_URL
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None
    REDIS_PRIVATE_URL: Optional[str] = None  # Railway 내부망 URL (egress 없음)
    REDIS_CACHE_HOST: str = "localhost"
    REDIS_CACHE_PORT: int = 6379
    REDIS_CACHE_DB: int = 1
    FILE_LIST_CACHE_TTL: int = 300
    FOLDER_LIST_CACHE_TTL: int = 300

    # 파일 저장소 경로 (Railway volume: /app/storage)
    STORAGE_BASE_PATH: str = "./storage"
    PDF_STORAGE_PATH: str = "./storage/pdf"
    CHUNKS_STORAGE_PATH: str = "./storage/chunks"
    CHROMADB_STORAGE_PATH: str = "./storage/chromadb"

    # Cloudflare R2 (S3 호환, 무료 10GB)
    # R2_ENDPOINT_URL: https://<account_id>.r2.cloudflarestorage.com
    R2_ENABLED: bool = False
    R2_BUCKET_NAME: Optional[str] = None
    R2_ENDPOINT_URL: Optional[str] = None
    R2_ACCESS_KEY: Optional[str] = None
    R2_SECRET_KEY: Optional[str] = None

    # AWS S3 (기존 호환용, R2 미사용 시)
    S3_ENABLED: bool = False
    S3_BUCKET_NAME: Optional[str] = None
    AWS_ACCESS_KEY: Optional[str] = None
    AWS_SECRET_KEY: Optional[str] = None
    AWS_REGION: str = "ap-northeast-2"

    # 프론트엔드 정적 파일 경로
    STATIC_DIR: str = "./frontend/dist"

    # AI 모델 (Gemini)
    GOOGLE_API_KEY: str = ""
    AI_API_KEY: str = ""  # deprecated — GOOGLE_API_KEY 사용
    AI_MODEL_NAME: str = "gemini-2.5-flash"
    AI_EMBEDDING_MODEL: str = "models/text-embedding-004"
    AI_LLM_TIMEOUT: int = 60  # LLM 요청 타임아웃 (초)

    # Kakao OAuth
    KAKAO_CLIENT_ID: str = ""
    KAKAO_CLIENT_SECRET: str = ""
    KAKAO_REDIRECT_URI: str = "https://api.planova.kr/api/v1/auth/kakao/callback"

    # CORS
    BACKEND_CORS_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://planova.kr",
        "https://api.planova.kr",
    ]

    # OAuth 토큰
    OAUTH_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # 결제/Iamport
    IAMPORT_WEBHOOK_SECRET: Optional[str] = None
    IAMPORT_API_KEY: str = ""
    IAMPORT_API_SECRET: str = ""
    IAMPORT_MERCHANT_ID: str = ""
    IAMPORT_CHANNEL_KEY: str = ""
    PORTONE_STORE_ID: Optional[str] = None
    PORTONE_CHANNEL_KEY: Optional[str] = None
    PORTONE_API_SECRET: Optional[str] = None
    PORTONE_CLIENT_KEY: Optional[str] = None

    # SMS
    SMS_API_KEY: Optional[str] = None
    SMS_API_SECRET: Optional[str] = None
    SMS_SENDER_NUMBER: Optional[str] = None

    # 이메일 (Gmail 앱 비밀번호 사용)
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "noreply@planova.kr"

    # 앱 설정
    API_BASE_URL: Optional[str] = None
    FRONTEND_URL: str = "https://planova.kr"
    ENVIRONMENT: str = "production"
    EMAIL_TEMPLATES_ENABLED: bool = True
    EMAIL_LOGO_URL: str = "https://planova.kr/logo.png"

    # 비밀번호 재설정
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    PASSWORD_RESET_TOKEN_LENGTH: int = 64

    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "allow"
    }

    @model_validator(mode='before')
    def assemble_connection_strings(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # DATABASE_URL (Railway) → DATABASE_URI 로 통일 (내부망 우선)
        if not values.get("DATABASE_URI"):
            if values.get("DATABASE_PRIVATE_URL"):
                values["DATABASE_URI"] = values["DATABASE_PRIVATE_URL"]
            elif values.get("DATABASE_URL"):
                values["DATABASE_URI"] = values["DATABASE_URL"]
            else:
                p_user = values.get("POSTGRES_USER", "postgres")
                p_pwd = values.get("POSTGRES_PASSWORD", "")
                p_host = values.get("POSTGRES_SERVER", "localhost")
                p_port = values.get("POSTGRES_PORT", 5432)
                p_db = values.get("POSTGRES_DB", "agent_db")
                if p_pwd:
                    values["DATABASE_URI"] = f"postgresql://{p_user}:{p_pwd}@{p_host}:{p_port}/{p_db}"

        # REDIS_URL 조합 (Railway 내부망 우선)
        if values.get("REDIS_PRIVATE_URL"):
            values["REDIS_URL"] = values["REDIS_PRIVATE_URL"]
        elif not values.get("REDIS_URL"):
            r_host = values.get("REDIS_HOST", "localhost")
            r_port = values.get("REDIS_PORT", 6379)
            r_db = values.get("REDIS_DB", 0)
            values["REDIS_URL"] = f"redis://{r_host}:{r_port}/{r_db}"

        return values

    @field_validator("BACKEND_CORS_ORIGINS", mode='before')
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str):
            if v.startswith("["):
                import json
                return json.loads(v)
            return [i.strip() for i in v.split(",")]
        return v

    @field_validator(
        "ACCESS_TOKEN_EXPIRE_MINUTES", "REFRESH_TOKEN_EXPIRE_DAYS",
        "OAUTH_REFRESH_TOKEN_EXPIRE_DAYS",
        "REDIS_PORT", "REDIS_DB", "REDIS_CACHE_DB",
        "FILE_LIST_CACHE_TTL", "FOLDER_LIST_CACHE_TTL",
        "POSTGRES_PORT", "SMTP_PORT",
        "PASSWORD_RESET_TOKEN_EXPIRE_MINUTES", "PASSWORD_RESET_TOKEN_LENGTH",
        mode='before'
    )
    @classmethod
    def parse_int_values(cls, v: Union[str, int]) -> int:
        return int(v) if isinstance(v, str) else v


settings = Settings()
