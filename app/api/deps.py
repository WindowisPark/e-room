# app/api/deps.py

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

import jwt
from jwt.exceptions import PyJWTError as JWTError
from pydantic import ValidationError
from sqlalchemy.orm import Session

import logging
from redis.exceptions import RedisError

from app import crud, schemas
from app.core.config import settings
from app.core.exceptions import ErrorMessage
from app.db.session import SessionLocal
from app.core.redis_helper import redis_client
from app.core.security import ACCESS_SECRET_KEY
from app.models.user import User

logger = logging.getLogger(__name__)

# OAuth2 스키마 수정 (카카오 콜백 후 토큰이 반환되므로 여기서는 별도 엔드포인트 필요 없음)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/kakao/callback",
    auto_error=False  # 토큰이 없을 때 자동 에러 방지
)

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessage.AUTH_REQUIRED,
            headers={"WWW-Authenticate": "Bearer"},
        )

    if redis_client is not None:
        try:
            if redis_client.exists(token):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=ErrorMessage.TOKEN_REVOKED,
                )
        except HTTPException:
            raise
        except RedisError as e:
            logger.warning(f"Redis 블랙리스트 확인 실패 (fail-open): {e}")
            # fail-open: Redis 장애 시 JWT exp로 보호

    try:
        payload = jwt.decode(token, ACCESS_SECRET_KEY, algorithms=["HS256"])
        token_data = schemas.TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessage.TOKEN_INVALID,
        )

    user = crud.user.get(db, id=token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorMessage.USER_NOT_FOUND,
        )
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not crud.user.is_active(current_user):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorMessage.USER_INACTIVE,
        )
    return current_user

def get_admin_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> User:
    """📌 관리자 권한 체크"""
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorMessage.ADMIN_REQUIRED,
        )
    return current_user

def get_storage_manager():
    """
    환경 설정에 따라 S3 또는 로컬 스토리지 관리자 반환
    """
    if settings.S3_ENABLED:
        from app.services.s3_file_service import S3StorageManager
        return S3StorageManager()
    else:
        from app.services.file_service import FileStorageManager
        return FileStorageManager()