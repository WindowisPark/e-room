#!/bin/bash
set -e

# Redis 헬스체크 (최대 30초 대기)
echo "Waiting for Redis..."
python - <<'EOF'
import os, time, sys
url = os.getenv("REDIS_PRIVATE_URL") or os.getenv("REDIS_URL") or f"redis://{os.getenv('REDIS_HOST','localhost')}:{os.getenv('REDIS_PORT','6379')}/0"
for i in range(15):
    try:
        import redis
        redis.from_url(url, socket_connect_timeout=2).ping()
        print("Redis is ready."); sys.exit(0)
    except Exception:
        print(f"Redis not ready, retrying ({i+1}/15)..."); time.sleep(2)
print("Redis connection timeout"); sys.exit(1)
EOF

# PostgreSQL 헬스체크 (최대 30초 대기)
echo "Waiting for PostgreSQL..."
python - <<'EOF'
import os, time, sys
url = os.getenv("DATABASE_PRIVATE_URL") or os.getenv("DATABASE_URL") or os.getenv("DATABASE_URI")
if not url:
    host = os.getenv("POSTGRES_SERVER", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    user = os.getenv("POSTGRES_USER", "postgres")
    pwd  = os.getenv("POSTGRES_PASSWORD", "")
    db   = os.getenv("POSTGRES_DB", "agent_db")
    url  = f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
for i in range(15):
    try:
        import psycopg2
        psycopg2.connect(url, connect_timeout=2).close()
        print("PostgreSQL is ready."); sys.exit(0)
    except Exception:
        print(f"PostgreSQL not ready, retrying ({i+1}/15)..."); time.sleep(2)
print("PostgreSQL connection timeout"); sys.exit(1)
EOF

echo "Running Alembic migrations..."
alembic upgrade head

echo "Starting server on port ${PORT:-8000}..."
exec gunicorn app.main:app \
    -k uvicorn.workers.UvicornWorker \
    -b "0.0.0.0:${PORT:-8000}" \
    --workers 2 \
    --timeout 120 \
    --keep-alive 5
