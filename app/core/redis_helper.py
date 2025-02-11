#app/core/redis_helper.py

import os
import logging
from redis import Redis, RedisError

# 로깅 설정
logger = logging.getLogger(__name__)

# 환경 변수에서 Redis 설정 로드
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# Redis 클라이언트 초기화
try:
    redis_client = Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    redis_client.ping()  # Redis 연결 확인
except RedisError as e:
    logger.error(f"⚠️ Redis 연결 실패: {str(e)}")
    redis_client = None  # 폴백 처리
