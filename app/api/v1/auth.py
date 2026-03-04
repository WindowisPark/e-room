# app/api/v1/auth.py 수정 버전

from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Body, Query
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
from app.core.exceptions import ErrorMessage
from app.models.user import User
from app.core.redis_helper import redis_client
import urllib.parse

# 🔐 비밀번호 재설정 관련 import 추가
from app.schemas.password_reset import (
    PasswordResetRequest, 
    PasswordResetResponse,
    PasswordResetConfirm, 
    PasswordResetConfirmResponse,
    TokenValidationRequest, 
    TokenValidationResponse,
    OAuthUserResetResponse
)
from app.services.password_reset_service import PasswordResetService
from app.schemas.local_auth import LocalUserCreate, RegisterResponse
from app.schemas.local_auth import LocalUserLogin, Token  # 추가

# 로깅 설정
logger = logging.getLogger(__name__)

router = APIRouter()

# 비밀번호 재설정 서비스 인스턴스 (기존 코드 뒤에 추가)
password_reset_service = PasswordResetService()

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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessage.REFRESH_TOKEN_INVALID,
        )

    stored_refresh_token = redis_client.get(f"refresh:{user_id}")

    # 🔧 decode() 오류 수정 → bytes일 경우만 decode
    if isinstance(stored_refresh_token, bytes):
        stored_refresh_token = stored_refresh_token.decode()

    if stored_refresh_token is None or stored_refresh_token != refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorMessage.REFRESH_TOKEN_INVALID,
        )

    new_access_token = security.create_access_token(user_id)
    logger.info(f"🔄 Access Token 재발급 - User ID: {user_id}")

    return {
        "access_token": new_access_token,
        "token_type": "bearer"
    }

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
                "token_type": "bearer",
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin,
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

@router.post("/kakao/token")
async def kakao_sdk_token_exchange(
    kakao_access_token: str = Body(..., embed=True),
    db: Session = Depends(deps.get_db)
):
    """
    카카오 FE SDK로 획득한 access_token을 받아 JWT 발급
    """
    async with httpx.AsyncClient() as client:
        try:
            user_info_response = await client.get(
                "https://kapi.kakao.com/v2/user/me",
                headers={"Authorization": f"Bearer {kakao_access_token}"},
                params={"property_keys": '["kakao_account.profile", "kakao_account.email", "kakao_account.name"]'}
            )
            user_info_response.raise_for_status()
            user_info = user_info_response.json()

            kakao_account = user_info.get("kakao_account", {})
            profile = kakao_account.get("profile", {})
            kakao_id = str(user_info.get("id"))

            if not kakao_id:
                raise HTTPException(status_code=400, detail="카카오 사용자 ID를 가져올 수 없습니다")

            nickname = profile.get("nickname")
            email = kakao_account.get("email")
            name = kakao_account.get("name")

            user = crud.user.get_by_oauth_id(db, "kakao", kakao_id)

            if not user:
                if not email:
                    email = f"kakao_{kakao_id}@example.com"
                display_name = name or nickname or "Kakao User"
                user_in = schemas.UserCreateOAuth(
                    oauth_provider="kakao",
                    oauth_id=kakao_id,
                    email=email,
                    full_name=display_name,
                    username=nickname or f"kakao_user_{kakao_id[:8]}",
                    is_verified=True
                )
                user = crud.user.create_oauth_user(db, obj_in=user_in)
                create_user_folders(user.id)
                logger.info(f"✅ 카카오 회원가입 성공 (SDK) - User ID: {user.id}")
            else:
                logger.info(f"✅ 카카오 로그인 성공 (SDK) - User ID: {user.id}")

            access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            refresh_token_expires = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
            access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
            refresh_token = security.create_refresh_token(user.id, expires_delta=refresh_token_expires)
            security.store_refresh_token(user.id, refresh_token, int(refresh_token_expires.total_seconds()))

            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "user_id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin,
            }

        except httpx.HTTPStatusError as e:
            logger.error(f"🚨 카카오 SDK 토큰 검증 오류: {str(e)}")
            raise HTTPException(status_code=401, detail="카카오 토큰 검증 실패")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"🚨 카카오 SDK 로그인 오류: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"인증 중 오류가 발생했습니다: {str(e)}")


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
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=ErrorMessage.EMAIL_ALREADY_EXISTS)

    existing_username = db.query(User).filter(User.username == user_in.username).first()
    if existing_username:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=ErrorMessage.USERNAME_ALREADY_EXISTS)

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

@router.post("/forgot-password", 
             response_model=PasswordResetResponse,
             summary="비밀번호 찾기 요청",
             description="이메일로 비밀번호 재설정 링크를 발송합니다.")
async def forgot_password(
    request: PasswordResetRequest,
    db: Session = Depends(deps.get_db)
):
    """
    📧 비밀번호 찾기 요청
    
    - 등록된 이메일로 재설정 링크 발송
    - OAuth 사용자는 해당 서비스 안내
    - 보안상 존재하지 않는 이메일도 성공 메시지 반환
    - 토큰 유효시간: 30분
    """
    try:
        result = await password_reset_service.request_password_reset(
            db=db, 
            email=request.email
        )
        
        # OAuth 사용자인 경우 별도 응답
        if not result["success"] and result.get("oauth_provider"):
            return OAuthUserResetResponse(
                message=result["message"],
                oauth_provider=result["oauth_provider"],
                redirect_url=result.get("redirect_url")
            )
        
        # 일반적인 실패 (이메일 발송 실패 등)
        if not result["success"]:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result["message"]
            )
        
        # 성공 응답
        return PasswordResetResponse(
            message=result["message"],
            email=result["email"],
            token_expires_in_minutes=result.get("token_expires_in_minutes")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"비밀번호 찾기 요청 처리 중 예외: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
        )


@router.post("/validate-reset-token", 
             response_model=TokenValidationResponse,
             summary="재설정 토큰 유효성 검사",
             description="비밀번호 재설정 토큰이 유효한지 확인합니다.")
async def validate_reset_token(
    request: TokenValidationRequest,
    db: Session = Depends(deps.get_db)
):
    """
    🔍 비밀번호 재설정 토큰 유효성 검사
    
    - 프론트엔드에서 재설정 페이지 로드 시 호출
    - 토큰 만료 여부 및 사용 여부 확인
    - 유효한 경우 만료 시간 정보 제공
    """
    try:
        result = password_reset_service.validate_reset_token(
            db=db, 
            token=request.token
        )
        
        return TokenValidationResponse(
            valid=result["valid"],
            message=result["message"],
            expires_at=result.get("expires_at")
        )
        
    except Exception as e:
        logger.error(f"토큰 검증 중 예외: {str(e)}", exc_info=True)
        return TokenValidationResponse(
            valid=False,
            message="토큰 검증 중 오류가 발생했습니다.",
            expires_at=None
        )


@router.post("/reset-password", 
             response_model=PasswordResetConfirmResponse,
             summary="비밀번호 재설정 실행",
             description="유효한 토큰으로 새 비밀번호로 변경합니다.")
async def reset_password(
    request: PasswordResetConfirm,
    db: Session = Depends(deps.get_db)
):
    """
    🔄 비밀번호 재설정 실행
    
    - 토큰 검증 후 새 비밀번호로 변경
    - 토큰은 사용 후 즉시 무효화
    - 해당 사용자의 다른 유효한 토큰들도 모두 무효화
    - 비밀번호 강도 검증 포함
    """
    try:
        result = password_reset_service.reset_password(
            db=db,
            token=request.token,
            new_password=request.new_password
        )
        
        if not result["success"]:
            # 토큰 관련 오류는 400 Bad Request
            if any(keyword in result["message"].lower() 
                   for keyword in ["토큰", "만료", "사용"]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=result["message"]
                )
            # 기타 오류는 500 Internal Server Error  
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=result["message"]
                )
        
        return PasswordResetConfirmResponse(
            message=result["message"],
            success=result["success"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"비밀번호 재설정 중 예외: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="비밀번호 재설정 중 오류가 발생했습니다."
        )


# ========== 관리자용 엔드포인트 (선택사항) ==========

@router.get("/admin/password-reset-history/{user_id}",
           summary="비밀번호 재설정 이력 조회 (관리자 전용)",
           description="특정 사용자의 비밀번호 재설정 이력을 조회합니다.")
async def get_password_reset_history(
    user_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(deps.get_admin_user)  # 관리자 권한 필요
):
    """
    📊 비밀번호 재설정 이력 조회 (관리자 전용)
    
    - 특정 사용자의 재설정 시도 이력
    - 보안 모니터링 및 분석용
    - 관리자만 접근 가능
    """
    try:
        history = password_reset_service.get_user_reset_history(
            db=db,
            user_id=user_id,
            limit=limit
        )
        
        return {
            "user_id": user_id,
            "total_attempts": len(history),
            "history": history
        }
        
    except Exception as e:
        logger.error(f"재설정 이력 조회 중 예외: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="이력 조회 중 오류가 발생했습니다."
        )


@router.post("/admin/cleanup-expired-tokens",
            summary="만료된 토큰 정리 (관리자 전용)",
            description="만료된 비밀번호 재설정 토큰들을 정리합니다.")
async def cleanup_expired_tokens(
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(deps.get_admin_user)  # 관리자 권한 필요
):
    """
    🧹 만료된 토큰 정리 (관리자 전용)
    
    - 1시간 이상 만료된 토큰들 삭제
    - 데이터베이스 용량 관리
    - 배치 작업으로도 실행 가능
    """
    try:
        deleted_count = password_reset_service.cleanup_expired_tokens(db)
        
        return {
            "message": f"만료된 토큰 {deleted_count}개가 정리되었습니다.",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"토큰 정리 중 예외: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="토큰 정리 중 오류가 발생했습니다."
        )