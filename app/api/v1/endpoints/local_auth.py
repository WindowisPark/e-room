# ✅ app/api/v1/endpoints/local_auth.py
from datetime import timedelta
import logging
from typing import Any

from fastapi import APIRouter, Body, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app import crud, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.schemas.local_auth import LocalUserCreate, LocalUserLogin, Token, RegisterResponse

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/register", response_model=RegisterResponse)
async def register_user(
    user_in: LocalUserCreate,
    db: Session = Depends(deps.get_db)
):
    existing_user = crud.user.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")

    existing_username = db.query(schemas.User).filter(schemas.User.username == user_in.username).first()
    if existing_username:
        raise HTTPException(status_code=400, detail="이미 사용 중인 사용자명입니다")

    user_schema = schemas.UserCreate(
        email=user_in.email,
        username=user_in.username,
        password=user_in.password,
        full_name=user_in.full_name
    )
    user = crud.user.create(db, obj_in=user_schema)

    if user_in.phone_number:
        crud.user.update(db, db_obj=user, obj_in={"phone_number": user_in.phone_number})

    try:
        from app.api.v1.auth import create_user_folders
        create_user_folders(user.id)
    except Exception as e:
        logger.error(f"기본 폴더 생성 실패: {str(e)}")

    return {
        "user_id": user.id,
        "email": user.email,
        "username": user.username,
        "message": "회원가입이 완료되었습니다"
    }

@router.post("/login", response_model=Token)
async def login_user(
    login_data: LocalUserLogin,
    db: Session = Depends(deps.get_db)
):
    user = crud.user.authenticate(db, email=login_data.email, password=login_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다")
    if not crud.user.is_active(user):
        raise HTTPException(status_code=400, detail="계정이 비활성화되었습니다")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
    refresh_token = security.create_refresh_token(user.id, expires_delta=refresh_token_expires)

    from app.core.security import store_refresh_token
    store_refresh_token(user.id, refresh_token, int(refresh_token_expires.total_seconds()))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin
    }

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(deps.get_db)
):
    user = crud.user.authenticate(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다")
    if not crud.user.is_active(user):
        raise HTTPException(status_code=400, detail="계정이 비활성화되었습니다")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
    refresh_token = security.create_refresh_token(user.id, expires_delta=refresh_token_expires)

    from app.core.security import store_refresh_token
    store_refresh_token(user.id, refresh_token, int(refresh_token_expires.total_seconds()))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin
    }