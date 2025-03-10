# app/api/v1/auth.py

from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
import httpx
import os
import logging

from fastapi.security import OAuth2PasswordRequestForm
from app import crud, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.core.redis_helper import redis_client
import urllib.parse

# 로깅 설정
logger = logging.getLogger(__name__)

router = APIRouter()

def create_user_folders(user_id: int):
    """
    새로 가입한 사용자의 기본 폴더 (study, exam) 생성
    """
    user_storage_path = f"storage/users/{user_id}"
    os.makedirs(user_storage_path, exist_ok=True)
    for category in ["study", "exam"]:
        os.makedirs(os.path.join(user_storage_path, category), exist_ok=True)

@router.post("/login", response_model=schemas.Token)
async def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    로그인 API - Access Token & Refresh Token 발급
    """
    user = crud.user.authenticate(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
    refresh_token = security.create_refresh_token(user.id, expires_delta=refresh_token_expires)

    security.store_refresh_token(user.id, refresh_token, int(refresh_token_expires.total_seconds()))

    logger.info(f"✅ 로그인 성공 - User ID: {user.id}")
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh-token")
async def refresh_token(refresh_token: str = Body(...)):
    """
    Refresh Token을 이용해 Access Token 재발급
    """
    user_id = security.verify_refresh_token(refresh_token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    stored_refresh_token = redis_client.get(f"refresh:{user_id}")
    if stored_refresh_token is None or stored_refresh_token.decode() != refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or invalid")

    new_access_token = security.create_access_token(user_id)
    logger.info(f"🔄 Access Token 재발급 - User ID: {user_id}")

    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post("/signup", response_model=schemas.User)
def signup(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
) -> Any:
    """
    일반 회원가입 API
    회원가입 후 기본 폴더 (study, exam) 생성
    """
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    # 유저 생성
    user = crud.user.create(db, obj_in=user_in)

    # 기본 폴더 생성
    create_user_folders(user.id)
    return user

@router.get("/google/authorize")
async def google_authorize():
    """
    Get Google OAuth2 authorization URL
    """
    encoded_redirect_uri = urllib.parse.quote(settings.GOOGLE_REDIRECT_URI, safe=':/')  # ✅ URL 인코딩 적용

    return {
        "authorization_url": f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"response_type=code&client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={encoded_redirect_uri}"
        f"&scope=openid email profile"
    }

# app/api/v1/auth.py

from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
import httpx
import os
import logging

from fastapi.security import OAuth2PasswordRequestForm
from app import crud, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.core.redis_helper import redis_client
import urllib.parse

# 로깅 설정
logger = logging.getLogger(__name__)

router = APIRouter()

def create_user_folders(user_id: int):
    """
    새로 가입한 사용자의 기본 폴더 (study, exam) 생성
    """
    user_storage_path = f"storage/users/{user_id}"
    os.makedirs(user_storage_path, exist_ok=True)
    for category in ["study", "exam"]:
        os.makedirs(os.path.join(user_storage_path, category), exist_ok=True)

@router.post("/login", response_model=schemas.Token)
async def login(
    db: Session = Depends(deps.get_db),
    form_data: OAuth2PasswordRequestForm = Depends()
):
    """
    로그인 API - Access Token & Refresh Token 발급
    """
    user = crud.user.authenticate(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
    refresh_token = security.create_refresh_token(user.id, expires_delta=refresh_token_expires)

    security.store_refresh_token(user.id, refresh_token, int(refresh_token_expires.total_seconds()))

    logger.info(f"✅ 로그인 성공 - User ID: {user.id}")
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.post("/refresh-token")
async def refresh_token(refresh_token: str = Body(...)):
    """
    Refresh Token을 이용해 Access Token 재발급
    """
    user_id = security.verify_refresh_token(refresh_token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    stored_refresh_token = redis_client.get(f"refresh:{user_id}")
    if stored_refresh_token is None or stored_refresh_token.decode() != refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expired or invalid")

    new_access_token = security.create_access_token(user_id)
    logger.info(f"🔄 Access Token 재발급 - User ID: {user_id}")

    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post("/signup", response_model=schemas.User)
def signup(
    *,
    db: Session = Depends(deps.get_db),
    user_in: schemas.UserCreate,
) -> Any:
    """
    일반 회원가입 API
    회원가입 후 기본 폴더 (study, exam) 생성
    """
    user = crud.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(
            status_code=400,
            detail="The user with this email already exists in the system.",
        )
    # 유저 생성
    user = crud.user.create(db, obj_in=user_in)

    # 기본 폴더 생성
    create_user_folders(user.id)
    return user

@router.get("/google/authorize")
async def google_authorize():
    """
    Get Google OAuth2 authorization URL
    """
    encoded_redirect_uri = urllib.parse.quote(settings.GOOGLE_REDIRECT_URI, safe=':/')  # ✅ URL 인코딩 적용

    return {
        "authorization_url": f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"response_type=code&client_id={settings.GOOGLE_CLIENT_ID}"
        f"&redirect_uri={encoded_redirect_uri}"
        f"&scope=openid email profile"
    }

@router.get("/google/callback")
async def google_callback(
    code: str,
    db: Session = Depends(deps.get_db)
):
    """
    Process Google OAuth2 callback
    """
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "code": code,
        "grant_type": "authorization_code",
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, data=token_data)
        token_response.raise_for_status()
        token_info = token_response.json()

        user_info_response = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {token_info['access_token']}"},
        )
        user_info = user_info_response.json()

    user = crud.user.get_by_oauth_id(db, "google", user_info["sub"])
    if not user:
        user_in = schemas.UserCreateOAuth(
            email=user_info["email"],
            full_name=user_info.get("name"),
            oauth_provider="google",
            oauth_id=user_info["sub"],
        )
        user = crud.user.create_oauth_user(db, obj_in=user_in)

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)

    refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = security.create_refresh_token(user.id, expires_delta=refresh_token_expires)

    security.store_refresh_token(user.id, refresh_token, int(refresh_token_expires.total_seconds()))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=schemas.User)
async def read_users_me(
    current_user: schemas.User = Depends(deps.get_current_user)
):
    """
    Get current user information
    """
    return current_user

@router.get("/naver/authorize")
async def naver_authorize():
    encoded_redirect_uri = urllib.parse.quote(settings.NAVER_REDIRECT_URI, safe=':/')  # ✅ URL 인코딩 적용

    return {
        "authorization_url": (
            "https://nid.naver.com/oauth2.0/authorize?"
            f"response_type=code&client_id={settings.NAVER_CLIENT_ID}"
            f"&redirect_uri={encoded_redirect_uri}"
            f"&state=RANDOM_STATE"
            f"&scope=email"
        )
    }


@router.get("/naver/callback")
async def naver_callback(
    code: str,
    state: str,
    db: Session = Depends(deps.get_db)
):
    # 네이버 토큰 엔드포인트로 인증 코드 교환
    token_url = "https://nid.naver.com/oauth2.0/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": settings.NAVER_CLIENT_ID,
        "client_secret": settings.NAVER_CLIENT_SECRET,
        "code": code,
        "state": state
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, data=token_data)
        token_info = token_response.json()

        # 네이버 사용자 정보 가져오기
        user_info_response = await client.get(
            "https://openapi.naver.com/v1/nid/me",
            headers={"Authorization": f"Bearer {token_info['access_token']}"},
        )
        user_info = user_info_response.json()
        naver_account = user_info.get("response", {})

        # 기존 OAuth 사용자 확인
        user = crud.user.get_by_oauth_id(db, "naver", naver_account.get("id"))
        if not user:
            user_in = schemas.UserCreateOAuth(
                oauth_provider="naver",
                oauth_id=naver_account.get("id"),
                full_name=naver_account.get("name"),
                is_verified=False
            )
            if naver_account.get("email"):
                user_in.email = naver_account.get("email")
            user = crud.user.create_oauth_user(db, obj_in=user_in)

        # 액세스 토큰 생성
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            user.id, expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

@router.get("/kakao/authorize")
async def kakao_authorize():
    """
    Get Kakao OAuth2 authorization URL
    """

    encoded_redirect_uri = urllib.parse.quote(settings.KAKAO_REDIRECT_URI, safe=':/')  # ✅ URL 인코딩 적용

    return {
        "authorization_url": (
            "https://kauth.kakao.com/oauth/authorize?"
            f"client_id={settings.KAKAO_CLIENT_ID}"
            f"&redirect_uri={encoded_redirect_uri}"
            f"&response_type=code"
        )
    }

@router.get("/kakao/callback")
async def kakao_callback(
    code: str,
    db: Session = Depends(deps.get_db)
):
    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": settings.KAKAO_CLIENT_ID,
        "client_secret": settings.KAKAO_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.KAKAO_REDIRECT_URI
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, data=token_data)
        token_info = token_response.json()

        # 카카오 사용자 정보 가져오기
        user_info_response = await client.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {token_info['access_token']}"},
        )
        user_info = user_info_response.json()
        
        # 사용자 정보 처리
        kakao_account = user_info.get("kakao_account", {})
        profile = kakao_account.get("profile", {})

        user = crud.user.get_by_oauth_id(db, "kakao", str(user_info.get("id")))
        if not user:
            user_in = schemas.UserCreateOAuth(
                oauth_provider="kakao",
                oauth_id=str(user_info.get("id")),
                email=kakao_account.get("email"),
                full_name=profile.get("nickname"),
                is_verified=False
            )
            user = crud.user.create_oauth_user(db, obj_in=user_in)

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            user.id, expires_delta=access_token_expires
        )

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
@router.post("/complete-profile", response_model=schemas.User)
async def complete_profile(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    user_update: schemas.UserProfileUpdate
):
    """
    OAuth 로그인 후 필요한 추가 정보를 입력받습니다.
    """
    if current_user.is_verified:
        raise HTTPException(
            status_code=400,
            detail="Profile is already complete"
        )
        
    user_data = user_update.dict(exclude_unset=True)
    user_data["is_verified"] = True
    updated_user = crud.user.update(db, db_obj=current_user, obj_in=user_data)
    return updated_user

@router.post("/logout")
async def logout(current_user: schemas.User = Depends(deps.get_current_user)):
    """
    로그아웃 API - Refresh Token 삭제
    """
    try:
        security.delete_refresh_token(current_user.id)
    except Exception as e:
        logger.error(f"🚨 로그아웃 시 Refresh Token 삭제 실패 - User ID: {current_user.id}, Error: {str(e)}")
        return {"msg": "Logout failed, but access revoked"}

    logger.info(f"🚪 로그아웃 - User ID: {current_user.id}")
    return {"msg": "Successfully logged out"}

@router.get("/me", response_model=schemas.User)
async def read_users_me(
    current_user: schemas.User = Depends(deps.get_current_user)
):
    """
    Get current user information
    """
    return current_user

@router.get("/naver/authorize")
async def naver_authorize():
    encoded_redirect_uri = urllib.parse.quote(settings.NAVER_REDIRECT_URI, safe=':/')  # ✅ URL 인코딩 적용

    return {
        "authorization_url": (
            "https://nid.naver.com/oauth2.0/authorize?"
            f"response_type=code&client_id={settings.NAVER_CLIENT_ID}"
            f"&redirect_uri={encoded_redirect_uri}"
            f"&state=RANDOM_STATE"
            f"&scope=email"
        )
    }


@router.get("/naver/callback")
async def naver_callback(
    code: str,
    state: str,
    db: Session = Depends(deps.get_db)
):
    # 네이버 토큰 엔드포인트로 인증 코드 교환
    token_url = "https://nid.naver.com/oauth2.0/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": settings.NAVER_CLIENT_ID,
        "client_secret": settings.NAVER_CLIENT_SECRET,
        "code": code,
        "state": state
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, data=token_data)
        token_info = token_response.json()

        # 네이버 사용자 정보 가져오기
        user_info_response = await client.get(
            "https://openapi.naver.com/v1/nid/me",
            headers={"Authorization": f"Bearer {token_info['access_token']}"},
        )
        user_info = user_info_response.json()
        naver_account = user_info.get("response", {})

        # 기존 OAuth 사용자 확인
        user = crud.user.get_by_oauth_id(db, "naver", naver_account.get("id"))
        if not user:
            user_in = schemas.UserCreateOAuth(
                oauth_provider="naver",
                oauth_id=naver_account.get("id"),
                full_name=naver_account.get("name"),
                is_verified=False
            )
            if naver_account.get("email"):
                user_in.email = naver_account.get("email")
            user = crud.user.create_oauth_user(db, obj_in=user_in)
            
            # 새 사용자인 경우 기본 폴더 생성
            create_user_folders(user.id)

        # 액세스 토큰 생성
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
        
        # refresh token 생성 및 저장
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = security.create_refresh_token(user.id, expires_delta=refresh_token_expires)
        security.store_refresh_token(user.id, refresh_token, int(refresh_token_expires.total_seconds()))

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
    
@router.get("/kakao/authorize")
async def kakao_authorize():
    """
    Get Kakao OAuth2 authorization URL
    """

    encoded_redirect_uri = urllib.parse.quote(settings.KAKAO_REDIRECT_URI, safe=':/')  # ✅ URL 인코딩 적용

    return {
        "authorization_url": (
            "https://kauth.kakao.com/oauth/authorize?"
            f"client_id={settings.KAKAO_CLIENT_ID}"
            f"&redirect_uri={encoded_redirect_uri}"
            f"&response_type=code"
        )
    }

@router.get("/kakao/callback")
async def kakao_callback(
    code: str,
    db: Session = Depends(deps.get_db)
):
    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": settings.KAKAO_CLIENT_ID,
        "client_secret": settings.KAKAO_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.KAKAO_REDIRECT_URI
    }

    async with httpx.AsyncClient() as client:
        token_response = await client.post(token_url, data=token_data)
        token_info = token_response.json()

        # 카카오 사용자 정보 가져오기
        user_info_response = await client.get(
            "https://kapi.kakao.com/v2/user/me",
            headers={"Authorization": f"Bearer {token_info['access_token']}"},
        )
        user_info = user_info_response.json()
        
        # 사용자 정보 처리
        kakao_account = user_info.get("kakao_account", {})
        profile = kakao_account.get("profile", {})

        user = crud.user.get_by_oauth_id(db, "kakao", str(user_info.get("id")))
        if not user:
            user_in = schemas.UserCreateOAuth(
                oauth_provider="kakao",
                oauth_id=str(user_info.get("id")),
                email=kakao_account.get("email"),
                full_name=profile.get("nickname"),
                is_verified=False
            )
            user = crud.user.create_oauth_user(db, obj_in=user_in)
            
            # 새 사용자인 경우 기본 폴더 생성
            create_user_folders(user.id)

        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(
            user.id, expires_delta=access_token_expires
        )
        
        # refresh token 생성 및 저장
        refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        refresh_token = security.create_refresh_token(user.id, expires_delta=refresh_token_expires)
        security.store_refresh_token(user.id, refresh_token, int(refresh_token_expires.total_seconds()))

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }
       
@router.post("/complete-profile", response_model=schemas.User)
async def complete_profile(
    *,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
    user_update: schemas.UserProfileUpdate
):
    """
    OAuth 로그인 후 필요한 추가 정보를 입력받습니다.
    """
    if current_user.is_verified:
        raise HTTPException(
            status_code=400,
            detail="Profile is already complete"
        )
        
    user_data = user_update.dict(exclude_unset=True)
    user_data["is_verified"] = True
    updated_user = crud.user.update(db, db_obj=current_user, obj_in=user_data)
    return updated_user

@router.post("/logout")
async def logout(current_user: schemas.User = Depends(deps.get_current_user)):
    """
    로그아웃 API - Refresh Token 삭제
    """
    try:
        security.delete_refresh_token(current_user.id)
    except Exception as e:
        logger.error(f"🚨 로그아웃 시 Refresh Token 삭제 실패 - User ID: {current_user.id}, Error: {str(e)}")
        return {"msg": "Logout failed, but access revoked"}

    logger.info(f"🚪 로그아웃 - User ID: {current_user.id}")
    return {"msg": "Successfully logged out"}