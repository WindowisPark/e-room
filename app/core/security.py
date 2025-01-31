# ai-agent/app/core/security.py

from datetime import datetime, timedelta
from typing import Any, Union, Optional
from jose import jwt
from passlib.context import CryptContext
from redis import Redis
from app.core.config import settings
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 환경 변수에서 REDIS_HOST 가져오기 (Docker Compose에서 설정됨)
REDIS_HOST = os.getenv("REDIS_HOST", "redis")

redis_client = Redis(host=REDIS_HOST, port=6379, db=0)

def create_access_token(subject: Union[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.SECRET_KEY, 
        algorithm="HS256"
    )
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)