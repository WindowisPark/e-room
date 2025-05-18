# app/api/v1/auth.py 수정 버전

from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import httpx
import os
import logging
import json  # JSON 모듈 추가 (누락됨)

from app import crud, schemas
from app.api import deps
from app.core import security
from app.core.config import settings
from app.models.user import User
from app.core.redis_helper import redis_client
import urllib.parse

from app.schemas.local_auth import LocalUserCreate, RegisterResponse
from app.schemas.local_auth import LocalUserLogin, Token  # 추가

# 로깅 설정
logger = logging.getLogger(__name__)

router = APIRouter()

# startup 이벤트 제거 (local_auth 관련 로직 분리)
# @router.on_event("startup")
# async def ensure_local_auth_attached():
#     router.include_router(local_auth.router, prefix="/local", tags=["로컬 인증"])

def create_user_folders(user_id: int):
    """
    새로 가입한 사용자의 기본 폴더 (study, exam) 생성
    """
    user_storage_path = f"storage/users/{user_id}"
    os.makedirs(user_storage_path, exist_ok=True)
    for category in ["study", "exam"]:
        os.makedirs(os.path.join(user_storage_path, category), exist_ok=True)

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

@router.get("/kakao/authorize")
async def kakao_authorize():
    """
    카카오 OAuth2 인증 URL 생성 - 동의 항목 설정에 맞게 수정
    """
    encoded_redirect_uri = urllib.parse.quote(settings.KAKAO_REDIRECT_URI, safe=':/')
    
    # 동의 항목은 카카오 개발자 콘솔의 설정과 일치시킴
    authorization_url = (
        "https://kauth.kakao.com/oauth/authorize?"
        f"client_id={settings.KAKAO_CLIENT_ID}"
        f"&redirect_uri={encoded_redirect_uri}"
        f"&response_type=code"
        f"&scope=profile_nickname,profile_image,account_email,name,phone_number"
    )
    
    logger.info(f"카카오 인증 URL 생성: {authorization_url}")
    
    return {
        "authorization_url": authorization_url
    }

@router.get("/kakao/callback")
async def kakao_callback(
    code: str,
    db: Session = Depends(deps.get_db)
):
    """
    카카오 OAuth2 콜백 처리 및 사용자 로그인/회원가입 관리
    """
    token_url = "https://kauth.kakao.com/oauth/token"
    token_data = {
        "grant_type": "authorization_code",
        "client_id": settings.KAKAO_CLIENT_ID,
        "client_secret": settings.KAKAO_CLIENT_SECRET,
        "code": code,
        "redirect_uri": settings.KAKAO_REDIRECT_URI
    }

    # 요청 데이터 로깅 추가
    logger.info(f"카카오 토큰 요청: {token_url}")
    logger.info(f"카카오 인증 정보: client_id={settings.KAKAO_CLIENT_ID}, redirect_uri={settings.KAKAO_REDIRECT_URI}")

    async with httpx.AsyncClient() as client:
        try:
            # 카카오 토큰 요청
            token_response = await client.post(token_url, data=token_data)
            
            # 응답 상태 코드 및 내용 로깅
            logger.info(f"토큰 응답 상태: {token_response.status_code}")
            if token_response.status_code != 200:
                logger.error(f"토큰 응답 에러: {token_response.text}")
                
            token_response.raise_for_status()
            token_info = token_response.json()
            logger.info(f"토큰 정보: {token_info}")

            # 카카오 사용자 정보 가져오기
            user_info_response = await client.get(
                "https://kapi.kakao.com/v2/user/me",
                headers={"Authorization": f"Bearer {token_info['access_token']}"},
                params={"property_keys": '["kakao_account.profile", "kakao_account.email", "kakao_account.name", "kakao_account.phone_number"]'}
            )
            user_info_response.raise_for_status()
            user_info = user_info_response.json()
            logger.info(f"사용자 정보: {json.dumps(user_info, indent=2, ensure_ascii=False)}")
            
            # 사용자 정보 처리 - 동의 항목에 맞게 수정
            kakao_account = user_info.get("kakao_account", {})
            profile = kakao_account.get("profile", {})
            kakao_id = str(user_info.get("id"))
            
            if not kakao_id:
                raise HTTPException(
                    status_code=400,
                    detail="카카오 사용자 ID를 가져올 수 없습니다"
                )

            # 동의 항목에서 데이터 추출 (있을 수도, 없을 수도 있음)
            nickname = profile.get("nickname")
            profile_image = profile.get("profile_image_url")
            email = kakao_account.get("email")
            name = kakao_account.get("name")
            phone_number = kakao_account.get("phone_number")
            
            # 기존 사용자인지 확인
            user = crud.user.get_by_oauth_id(db, "kakao", kakao_id)
            
            # 새 사용자라면 등록
            if not user:
                # 필수 정보 확인 및 대체값 설정
                if not email:
                    email = f"kakao_{kakao_id}@example.com"  # 이메일 없는 경우 대체값
                
                # 표시 이름은 실명 > 닉네임 > 기본값 순으로 사용
                display_name = name or nickname or "Kakao User"
                
                user_in = schemas.UserCreateOAuth(
                    oauth_provider="kakao",
                    oauth_id=kakao_id,
                    email=email,
                    full_name=display_name,
                    username=nickname or f"kakao_user_{kakao_id[:8]}", # 닉네임을 사용자명으로
                    phone_number=phone_number,  # 전화번호 필드 추가
                    is_verified=True  # 카카오 인증은 기본적으로 verified 상태
                )
                
                user = crud.user.create_oauth_user(db, obj_in=user_in)
                
                # 새 사용자인 경우 기본 폴더 생성
                create_user_folders(user.id)
                
                logger.info(f"✅ 카카오 회원가입 성공 - User ID: {user.id}, Name: {display_name}")
            else:
                # 기존 사용자 정보 업데이트 (선택적)
                update_data = {}
                if phone_number and not user.phone_number:
                    update_data["phone_number"] = phone_number
                if nickname and not user.username:
                    update_data["username"] = nickname
                if name and not user.full_name:
                    update_data["full_name"] = name
                
                # 업데이트할 데이터가 있으면 적용
                if update_data:
                    crud.user.update(db, db_obj=user, obj_in=update_data)
                    logger.info(f"✅ 카카오 로그인 및 사용자 정보 업데이트 - User ID: {user.id}")
                else:
                    logger.info(f"✅ 카카오 로그인 성공 - User ID: {user.id}")

            # 토큰 생성
            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            
            access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
            refresh_token = security.create_refresh_token(user.id, expires_delta=refresh_token_expires)
            
            # Refresh 토큰 저장
            security.store_refresh_token(
                user.id, 
                refresh_token, 
                int(refresh_token_expires.total_seconds())
            )

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }
            
        except httpx.HTTPStatusError as e:
            # 응답 내용 로깅 추가
            error_detail = ""
            try:
                error_detail = e.response.json()
            except:
                error_detail = e.response.text
                
            logger.error(f"🚨 카카오 인증 오류: {str(e)}, 상세: {error_detail}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"카카오 인증 실패: {str(e)}, 상세: {error_detail}"
            )
        except Exception as e:
            logger.error(f"🚨 카카오 로그인/회원가입 오류: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"인증 중 오류가 발생했습니다: {str(e)}"
            )

@router.get("/me", response_model=schemas.User)
async def read_users_me(
    current_user: schemas.User = Depends(deps.get_current_user)
):
    """
    현재 사용자 정보 조회
    """
    return current_user

@router.post("/logout")
async def logout(current_user: schemas.User = Depends(deps.get_current_user)):
    """
    로그아웃 API - Refresh Token 삭제
    """
    try:
        security.delete_refresh_token(current_user.id)
    except Exception as e:
        logger.error(f"🚨 로그아웃 시 Refresh Token 삭제 실패 - User ID: {current_user.id}, Error: {str(e)}")
        return {"msg": "로그아웃 실패, 그러나 액세스는 취소됨"}

    logger.info(f"🚪 로그아웃 - User ID: {current_user.id}")
    return {"msg": "성공적으로 로그아웃되었습니다"}

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
        create_user_folders(user.id)
    except Exception as e:
        logger.warning(f"기본 폴더 생성 실패: {str(e)}")

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
    user = crud.user.authenticate(
        db, email=login_data.email, password=login_data.password
    )
    if not user or not crud.user.is_active(user):
        raise HTTPException(status_code=401, detail="인증 실패")

    access_token = security.create_access_token(user.id, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = security.create_refresh_token(user.id, expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    security.store_refresh_token(user.id, refresh_token, int(timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS).total_seconds()))

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
    if not user or not crud.user.is_active(user):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다")

    access_token = security.create_access_token(user.id, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    refresh_token = security.create_refresh_token(user.id, expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    security.store_refresh_token(user.id, refresh_token, int(timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS).total_seconds()))

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "is_admin": user.is_admin
    }