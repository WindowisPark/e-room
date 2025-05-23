from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from app.schemas.token import TokenPayload
from redis import Redis
from redis.exceptions import RedisError
from app.core.config import settings
from app.models.user import User
from app.db.session import get_db
from sqlalchemy.orm import Session

import os
import logging
import hmac
import hashlib
from fastapi import Request, HTTPException, WebSocket, status
from app.core.redis_helper import redis_client

# 로깅 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # 기본 로그 레벨 설정 (INFO 이상)

# Access & Refresh Token 각각의 시크릿 키 사용
ACCESS_SECRET_KEY = settings.ACCESS_SECRET_KEY
REFRESH_SECRET_KEY = settings.REFRESH_SECRET_KEY

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 환경 변수에서 REDIS_HOST 가져오기 (Docker Compose에서 설정됨)
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")


def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Access Token 생성 (일반 API 인증용)
    """
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, ACCESS_SECRET_KEY, algorithm="HS256")

def create_refresh_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Refresh Token 생성 (Redis에 저장됨)
    """
    expire = datetime.utcnow() + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode = {"exp": expire, "sub": str(subject)}
    return jwt.encode(to_encode, REFRESH_SECRET_KEY, algorithm="HS256")

def verify_refresh_token(token: str) -> Optional[int]:
    """
    Refresh Token 검증 및 Redis에서 체크
    """
    try:
        payload = jwt.decode(token, REFRESH_SECRET_KEY, algorithms=["HS256"])
        user_id = int(payload.get("sub"))

        # Redis에서 해당 Refresh Token이 유효한지 확인
        stored_refresh_token = redis_client.get(f"refresh:{user_id}") if redis_client else None

        # ✅ decode()는 bytes일 때만
        if isinstance(stored_refresh_token, bytes):
            stored_refresh_token = stored_refresh_token.decode()

        if stored_refresh_token is None or stored_refresh_token != token:
            logger.warning(f"Refresh Token이 Redis에 없음 또는 불일치 (User ID: {user_id})")
            return None

        return user_id

    except JWTError as e:
        logger.error(f"Refresh Token 검증 실패: {str(e)}")
        return None

def store_refresh_token(user_id: int, refresh_token: str, expires_in: int):
    """
    Redis에 Refresh Token 저장 (연결 실패 시 로깅만 하고 무시)
    """
    if redis_client:
        try:
            redis_client.setex(f"refresh:{user_id}", expires_in, refresh_token)
        except RedisError as e:
            logger.error(f"⚠️ Redis 저장 실패: {str(e)}")
    else:
        logger.warning(f"⚠️ Redis가 비활성화된 상태입니다. Refresh Token이 저장되지 않음 (User ID: {user_id})")

def delete_refresh_token(user_id: int):
    """
    Redis에서 Refresh Token 삭제
    """
    if redis_client:
        try:
            redis_client.delete(f"refresh:{user_id}")
        except RedisError as e:
            logger.error(f"⚠️ Redis 삭제 실패: {str(e)}")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

async def verify_iamport_webhook(request: Request):
    signature = request.headers.get("x-imp-signature")
    body = await request.body()  # await 사용이므로 async 함수 필요
    secret = settings.IAMPORT_WEBHOOK_SECRET.encode()

    generated_signature = hmac.new(secret, body, hashlib.sha256).hexdigest()

    if not hmac.compare_digest(signature, generated_signature):
        raise HTTPException(status_code=403, detail="Invalid Webhook Signature")

async def get_current_user_ws(websocket: WebSocket) -> Optional[User]:
    """
    WebSocket 요청에서 토큰을 추출하여 유효한 사용자인지 확인하고 반환
    """
    token = websocket.query_params.get("token")
    if not token:
        logger.warning("⚠️ WebSocket: 인증 토큰이 없습니다.")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="인증 필요")
        return None

    try:
        # JWT 디코드
        payload = jwt.decode(token, settings.ACCESS_SECRET_KEY, algorithms=["HS256"])
        token_data = TokenPayload(**payload)

        # 만료 확인
        if token_data.exp and datetime.fromtimestamp(token_data.exp) < datetime.utcnow():
            logger.warning("⚠️ WebSocket: 만료된 토큰")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="토큰 만료")
            return None

    except (JWTError, ValueError) as e:
        logger.error(f"❌ WebSocket: 토큰 검증 실패 - {str(e)}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="토큰 오류")
        return None

    try:
        user_id = int(token_data.sub) if token_data.sub else None
        if not user_id:
            logger.warning("⚠️ WebSocket: 토큰에 사용자 정보 없음")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="잘못된 토큰")
            return None

        db: Session = next(get_db())
        user = db.query(User).filter(User.id == user_id).first()

        if not user or not user.is_active:
            logger.warning(f"⚠️ WebSocket: 유효하지 않거나 비활성화된 사용자 (ID: {token_data.sub})")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="사용자 인증 실패")
            return None

        return user

    except Exception as e:
        logger.error(f"❌ WebSocket 사용자 조회 실패: {str(e)}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR, reason="서버 오류")
        return None
   