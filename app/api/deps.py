# app/api/deps.py

from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from jose import JWTError, jwt
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app import crud, schemas
from app.core.config import settings
from app.db.session import SessionLocal
from app.core.redis_helper import redis_client
from app.core.security import ACCESS_SECRET_KEY, redis_client
from app.models.user import User

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
            detail="인증이 필요합니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # 블랙리스트된 토큰 거부
    if redis_client.exists(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="토큰이 취소되었습니다"
        )

    try:
        payload = jwt.decode(token, ACCESS_SECRET_KEY, algorithms=["HS256"])
        token_data = schemas.TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="인증 정보를 확인할 수 없습니다"
        )

    user = crud.user.get(db, id=token_data.sub)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="사용자를 찾을 수 없습니다"
        )
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not crud.user.is_active(current_user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="비활성화된 사용자입니다"
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
            detail="관리자 권한이 필요합니다."
        )
    return current_user