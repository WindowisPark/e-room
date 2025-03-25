# app/api/v1/auth.py

from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session
import httpx
import os
import logging

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
    카카오 OAuth2 인증 URL 생성
    """
    encoded_redirect_uri = urllib.parse.quote(settings.KAKAO_REDIRECT_URI, safe=':/')

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

    async with httpx.AsyncClient() as client:
        try:
            # 카카오 토큰 요청
            token_response = await client.post(token_url, data=token_data)
            token_response.raise_for_status()
            token_info = token_response.json()

            # 카카오 사용자 정보 가져오기
            user_info_response = await client.get(
                "https://kapi.kakao.com/v2/user/me",
                headers={"Authorization": f"Bearer {token_info['access_token']}"},
            )
            user_info_response.raise_for_status()
            user_info = user_info_response.json()
            
            # 사용자 정보 처리
            kakao_account = user_info.get("kakao_account", {})
            profile = kakao_account.get("profile", {})
            kakao_id = str(user_info.get("id"))
            
            if not kakao_id:
                raise HTTPException(
                    status_code=400,
                    detail="카카오 사용자 ID를 가져올 수 없습니다"
                )

            # 기존 사용자인지 확인
            user = crud.user.get_by_oauth_id(db, "kakao", kakao_id)
            
            # 새 사용자라면 등록
            if not user:
                email = kakao_account.get("email")
                name = profile.get("nickname", "Kakao User")
                
                # 필수 정보 확인
                if not email:
                    email = f"kakao_{kakao_id}@example.com"  # 이메일 없는 경우 대체값
                
                user_in = schemas.UserCreateOAuth(
                    oauth_provider="kakao",
                    oauth_id=kakao_id,
                    email=email,
                    full_name=name,
                    # 카카오에서 제공하는 기본 정보로 verified 상태로 설정
                    is_verified=True
                )
                
                user = crud.user.create_oauth_user(db, obj_in=user_in)
                
                # 새 사용자인 경우 기본 폴더 생성
                create_user_folders(user.id)
                
                logger.info(f"✅ 카카오 회원가입 성공 - User ID: {user.id}")
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
            logger.error(f"🚨 카카오 인증 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"카카오 인증 실패: {str(e)}"
            )
        except Exception as e:
            logger.error(f"🚨 카카오 로그인/회원가입 오류: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="인증 중 오류가 발생했습니다"
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