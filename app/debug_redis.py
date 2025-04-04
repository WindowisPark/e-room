# debug_redis.py

import os
import redis
from dotenv import load_dotenv

# .env 파일 강제 로드 (환경변수 덮어쓰기 위해)
load_dotenv(override=True)

# 환경변수 출력
print("🔍 환경변수 확인")
print("REDIS_HOST:", os.getenv("REDIS_HOST"))
print("REDIS_PORT:", os.getenv("REDIS_PORT"))

# redis 연결 시도
host = os.getenv("REDIS_HOST", "localhost")
port = int(os.getenv("REDIS_PORT", 6379))

print(f"🚀 Redis 연결 시도 중... ({host}:{port})")

try:
    client = redis.Redis(host=host, port=port, decode_responses=True)
    client.ping()
    print("✅ Redis 연결 성공")
except redis.exceptions.ConnectionError as e:
    print(f"❌ Redis 연결 실패: {str(e)}")
