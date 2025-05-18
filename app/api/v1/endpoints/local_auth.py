# app/api/v1/endpoints/local_auth.py

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

# 로깅 설정
logger = logging.getLogger(__name__)

router = APIRouter(tags=["로컬 인증"])

@router.post("/register", response_model=RegisterResponse)
async def register_user(
    user_in: LocalUserCreate,
    db: Session = Depends(deps.get_db)
):
    """
    자체 회원가입 API
    
    - 이메일 중복 확인
    - 사용자 생성
    - 기본 폴더 생성
    """
    # 이메일 중복 확인
    existing_user = crud.user.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 등록된 이메일입니다"
        )
    
    # 사용자명 중복 확인
    existing_username = db.query(schemas.User).filter(schemas.User.username == user_in.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 사용 중인 사용자명입니다"
        )
    
    # 사용자 생성
    try:
        user_schema = schemas.UserCreate(
            email=user_in.email,
            username=user_in.username,
            password=user_in.password,
            full_name=user_in.full_name
        )
        user = crud.user.create(db, obj_in=user_schema)
        
        # 전화번호 정보가 있는 경우 추가 업데이트
        if user_in.phone_number:
            crud.user.update(db, db_obj=user, obj_in={"phone_number": user_in.phone_number})
        
        # 기본 폴더 생성
        try:
            from app.api.v1.auth import create_user_folders
            create_user_folders(user.id)
        except Exception as e:
            logger.error(f"기본 폴더 생성 실패: {str(e)}")
            # 폴더 생성은 실패해도 회원가입은 성공으로 처리
        
        logger.info(f"✅ 로컬 회원가입 성공 - User ID: {user.id}, Email: {user.email}")
        
        return {
            "user_id": user.id,
            "email": user.email,
            "username": user.username,
            "message": "회원가입이 완료되었습니다"
        }
        
    except Exception as e:
        logger.error(f"회원가입 처리 중 오류: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="회원가입 처리 중 오류가 발생했습니다"
        )


@router.post("/login", response_model=Token)
async def login_user(
    login_data: LocalUserLogin,
    db: Session = Depends(deps.get_db)
):
    """
    자체 로그인 API
    
    - 이메일/비밀번호 인증
    - JWT 토큰 발급
    """
    # 사용자 인증
    user = crud.user.authenticate(
        db, 
        email=login_data.email, 
        password=login_data.password
    )
    
    if not user:
        logger.warning(f"로그인 실패 - Email: {login_data.email} (이메일 또는 비밀번호 불일치)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not crud.user.is_active(user):
        logger.warning(f"비활성화 계정 로그인 시도 - Email: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="계정이 비활성화되었습니다"
        )
    
    # 토큰 생성
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
    refresh_token = security.create_refresh_token(user.id, expires_delta=refresh_token_expires)
    
    # Refresh 토큰 저장
    from app.core.security import store_refresh_token
    store_refresh_token(
        user.id,
        refresh_token,
        int(refresh_token_expires.total_seconds())
    )
    
    logger.info(f"✅ 로컬 로그인 성공 - User ID: {user.id}, Email: {user.email}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin
    }


# OAuth2PasswordRequestForm 호환 로그인 엔드포인트 (Swagger 문서화 지원)
@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(deps.get_db)
):
    """
    OAuth2 호환 로그인 엔드포인트 (Swagger UI 지원)
    """
    user = crud.user.authenticate(
        db, 
        email=form_data.username,  # OAuth2PasswordRequestForm은 username 필드 사용
        password=form_data.password
    )
    
    if not user:
        logger.warning(f"로그인 실패 - Email: {form_data.username} (이메일 또는 비밀번호 불일치)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not crud.user.is_active(user):
        logger.warning(f"비활성화 계정 로그인 시도 - Email: {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="계정이 비활성화되었습니다"
        )
    
    # 토큰 생성
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
    refresh_token = security.create_refresh_token(user.id, expires_delta=refresh_token_expires)
    
    # Refresh 토큰 저장
    from app.core.security import store_refresh_token
    store_refresh_token(
        user.id,
        refresh_token,
        int(refresh_token_expires.total_seconds())
    )
    
    logger.info(f"✅ OAuth 형식 로그인 성공 - User ID: {user.id}, Email: {user.email}")
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin
    }