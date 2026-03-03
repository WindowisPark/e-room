"""
alembic upgrade head을 .env 로드 후 실행하는 헬퍼 스크립트
"""
import os
import sys

# .env 파일 로드
env_path = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(env_path):
    with open(env_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())
    print(f"[OK] .env 로드 완료 ({env_path})")
else:
    print("[WARN] .env 파일 없음")

# 필수 환경변수 폴백 (마이그레이션 전용, JWT 기능 미사용)
os.environ.setdefault("SECRET_KEY", "dev-migration-secret-key")

# alembic upgrade head 실행
from alembic.config import Config
from alembic import command

alembic_cfg = Config(os.path.join(os.path.dirname(__file__), "alembic.ini"))
alembic_cfg.set_main_option("script_location", os.path.join(os.path.dirname(__file__), "alembic"))

# DB URI 확인 및 asyncpg → psycopg2 교체 (alembic은 sync 드라이버 필요)
from app.core.config import settings as app_settings
db_uri = app_settings.DATABASE_URI
if db_uri and "+asyncpg" in db_uri:
    db_uri = db_uri.replace("+asyncpg", "")
    print(f"[INFO] asyncpg → sync 드라이버로 교체: {db_uri}")
else:
    print(f"[INFO] DATABASE_URI: {db_uri}")
os.environ["DATABASE_URI"] = db_uri

print("[INFO] alembic upgrade head 실행 중...")
alembic_cfg.set_main_option("sqlalchemy.url", db_uri)
command.upgrade(alembic_cfg, "head")
print("[DONE] 마이그레이션 완료!")
