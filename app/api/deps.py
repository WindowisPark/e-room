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

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
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
) -> User:  # models.User → User로 변경
    # 추가: 블랙리스트된 토큰 거부
    if redis_client.exists(token):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    try:
        payload = jwt.decode(token, ACCESS_SECRET_KEY, algorithms=["HS256"])
        token_data = schemas.TokenPayload(**payload)
    except (JWTError, ValidationError):
        raise HTTPException(status_code=403, detail="Could not validate credentials")

    user = crud.user.get(db, id=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

def get_current_active_user(
    current_user: User = Depends(get_current_user),  # models.User → User로 변경
) -> User:  # models.User → User로 변경
    if not crud.user.is_active(current_user):
        raise HTTPException(
            status_code=400, 
            detail="Inactive user"
        )
    return current_user

def get_admin_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)  # deps.get_db → get_db로 변경
) -> User:
    """📌 관리자 권한 체크"""
    if current_user.role != "admin":  # is_admin 대신 role 체크
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다."
        )
    return current_user