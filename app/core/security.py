from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt, JWTError
from passlib.context import CryptContext
from redis import Redis
from redis.exceptions import RedisError
from app.core.config import settings
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
REDIS_HOST = os.getenv("REDIS_HOST", "redis")

# Redis 연결 (예외 처리 추가)
try:
    redis_client = Redis(host=REDIS_HOST, port=6379, db=0)
    redis_client.ping()  # 연결 확인
    logger.info("✅ Redis 연결 성공")
except Exception as e:
    logger.error(f"⚠️ Redis 연결 실패: {str(e)}")
    redis_client = None

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
        if stored_refresh_token is None or stored_refresh_token.decode() != token:
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

async def get_current_user_ws(websocket: WebSocket):
    """
    WebSocket 연결에서 토큰 검증 및 사용자 정보 가져오기
    
    참고: 순환 참조 문제를 해결하기 위해 필요한 모듈은 함수 내부에서 가져옵니다.
    """
    # 쿼리 파라미터에서 토큰 추출
    token = websocket.query_params.get("token")
    if not token:
        # 토큰이 없으면 연결 거부
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    
    try:
        # 토큰 검증 및 사용자 정보 조회 (ACCESS_SECRET_KEY 사용)
        payload = jwt.decode(
            token, ACCESS_SECRET_KEY, algorithms=["HS256"]
        )
        user_id = int(payload.get("sub"))
        
        # 토큰 만료 검증
        if "exp" not in payload or datetime.fromtimestamp(payload["exp"]) < datetime.utcnow():
            logger.warning(f"🚨 만료된 토큰으로 WebSocket 연결 시도")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None
            
    except (JWTError, ValueError) as e:
        # 토큰 검증 실패 시 연결 거부
        logger.error(f"🚨 WebSocket 토큰 검증 실패: {str(e)}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None
    
    try:
        # 순환 참조 방지를 위해 함수 내부에서 필요한 모듈 임포트
        from app.api.deps import get_db
        from app.crud.crud_user import get_user
        from pydantic import ValidationError
        
        # 데이터베이스에서 사용자 정보 조회
        db = next(get_db())
        user = get_user(db, id=user_id)
        
        if not user or not user.is_active:
            # 사용자가 없거나 비활성화 상태면 연결 거부
            logger.warning(f"🚨 비활성화된 사용자 또는 없는 사용자 ID: {user_id}")
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return None
        
        return user
        
    except Exception as e:
        logger.error(f"🚨 WebSocket 사용자 정보 조회 실패: {str(e)}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return None