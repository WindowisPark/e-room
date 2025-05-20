# app/core/config.py

import os
from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, field_validator, model_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # ✅ 프로젝트 기본 설정
    PROJECT_NAME: str = "AI-Agent API"
    API_V1_STR: str = "/api/v1"

    # ✅ PostgreSQL 설정
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5433
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password123"
    POSTGRES_DB: str = "agent_db"
    DATABASE_URI: Optional[str] = None

    # ✅ JWT 설정
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-default-secret-key")
    ACCESS_SECRET_KEY: str = os.getenv("ACCESS_SECRET_KEY", "access-secret-key-for-jwt")
    REFRESH_SECRET_KEY: str = os.getenv("REFRESH_SECRET_KEY", "refresh-secret-key-for-jwt")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

    # ✅ Redis 설정
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None  # 동적으로 조합

    # ✅ Redis 캐시 설정
    REDIS_CACHE_HOST: str = "localhost"
    REDIS_CACHE_PORT: int = 6379
    REDIS_CACHE_DB: int = 1
    FILE_LIST_CACHE_TTL: int = 300
    FOLDER_LIST_CACHE_TTL: int = 300

    # ✅ S3 설정 추가
    S3_ENABLED: bool = False  # 기본값은 False로 설정
    S3_BUCKET_NAME: Optional[str] = None
    AWS_ACCESS_KEY: Optional[str] = None
    AWS_SECRET_KEY: Optional[str] = None
    AWS_REGION: str = "ap-northeast-2"  # 기본 리전 설정 (한국/서울)

    # ✅ 스토리지 경로 설정
    STORAGE_BASE_PATH: str = "./storage"  # 도커 볼륨 마운트 기준점
    PDF_STORAGE_PATH: str = f"{STORAGE_BASE_PATH}"  # 사용자 ID 폴더 내에 PDF 저장
    CHUNKS_STORAGE_PATH: str = f"{STORAGE_BASE_PATH}/chunks"  # 기존 청크 저장 경로
    CHROMADB_STORAGE_PATH: str = f"{STORAGE_BASE_PATH}/chromadb"  # 새로운 ChromaDB 저장 경로
    # ✅ PDF Agent 설정
    PDF_STORAGE_PATH: str = "./storage/pdf"
    PDF_CHUNK_SIZE: int = 1000
    PDF_CHUNK_OVERLAP: int = 200

    # ✅ AI 모델 설정
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_MODEL_NAME: str = os.getenv("AI_MODEL_NAME", "gpt-3.5-turbo")
    AI_EMBEDDING_MODEL: str = os.getenv("AI_EMBEDDING_MODEL", "text-embedding-ada-002")

    # ✅ Kakao OAuth 설정
    KAKAO_CLIENT_ID: str = os.getenv("KAKAO_CLIENT_ID", "")
    KAKAO_CLIENT_SECRET: str = os.getenv("KAKAO_CLIENT_SECRET", "")
    KAKAO_REDIRECT_URI: str = "https://api.planova.kr/api/v1/auth/kakao/callback"

    # ✅ CORS 설정
    BACKEND_CORS_ORIGINS: Union[List[str], str] = ["http://localhost:3000", "http://localhost:8000"]

    # ✅ OAuth 토큰 만료
    OAUTH_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("OAUTH_REFRESH_TOKEN_EXPIRE_DAYS", "30"))

    # ✅ 결제/Iamport 설정
    IAMPORT_WEBHOOK_SECRET: str = ""
    IAMPORT_API_KEY: str = os.getenv("IAMPORT_API_KEY", "")
    IAMPORT_API_SECRET: str = os.getenv("IAMPORT_API_SECRET", "")
    IAMPORT_MERCHANT_ID: str = os.getenv("IAMPORT_MERCHANT_ID", "")
    IAMPORT_CHANNEL_KEY: str = os.getenv("IAMPORT_CHANNEL_KEY", "")

    # ✅ SMS 인증 설정
    SMS_API_KEY: Optional[str] = None
    SMS_API_SECRET: Optional[str] = None
    SMS_SENDER_NUMBER: Optional[str] = None

    # ✅ Pydantic Settings
    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "allow"
    }

    # ✅ DB 및 Redis URL 자동 조립
    @model_validator(mode='before')
    def assemble_connection_strings(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # PostgreSQL
        if not values.get("DATABASE_URI"):
            p_user = values.get("POSTGRES_USER")
            p_pwd = values.get("POSTGRES_PASSWORD")
            p_host = values.get("POSTGRES_SERVER")
            p_db = values.get("POSTGRES_DB")
            p_port = values.get("POSTGRES_PORT", 5432)
            if all([p_user, p_pwd, p_host, p_db]):
                values["DATABASE_URI"] = f"postgresql://{p_user}:{p_pwd}@{p_host}:{p_port}/{p_db}"

        # Redis
        if not values.get("REDIS_URL"):
            r_host = values.get("REDIS_HOST", "localhost")
            r_port = values.get("REDIS_PORT", 6379)
            r_db = values.get("REDIS_DB", 0)
            values["REDIS_URL"] = f"redis://{r_host}:{r_port}/{r_db}"

        return values

    # ✅ CORS origin 목록 파싱
    @field_validator("BACKEND_CORS_ORIGINS", mode='before')
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # ✅ int로 변환 필요한 항목 처리
    @field_validator(
        "ACCESS_TOKEN_EXPIRE_MINUTES",
        "REFRESH_TOKEN_EXPIRE_DAYS",
        "OAUTH_REFRESH_TOKEN_EXPIRE_DAYS",
        "REDIS_PORT", "REDIS_DB",
        "REDIS_CACHE_PORT", "REDIS_CACHE_DB",
        "FILE_LIST_CACHE_TTL", "FOLDER_LIST_CACHE_TTL",
        "POSTGRES_PORT",
        mode='before'
    )
    @classmethod
    def parse_int_values(cls, v: Union[str, int]) -> int:
        return int(v) if isinstance(v, str) else v


# ✅ 인스턴스 선언
settings = Settings()

# ✅ 확인용 출력 (배포 시 제거 가능)
print(f"Loaded DATABASE_URI: {settings.DATABASE_URI}")
print(f"Loaded REDIS_URL: {settings.REDIS_URL}")
print(f"Loaded CORS Origins: {settings.BACKEND_CORS_ORIGINS}")
