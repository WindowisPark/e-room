# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context

import sys
import os

# 프로젝트 루트 경로를 sys.path에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.db.base import Base

# 유지되는 모델만 import
from app.models.user import User
from app.models.tag import PDFFile, PDFTag
from app.models.password_reset import PasswordResetToken
from app.models.resume import ResumeProfile, ResumeItem
from app.models.job_research import SavedCompany
from app.models.cover_letter import CoverLetter, CoverLetterItem

# Alembic 설정
config = context.config

# asyncpg 드라이버는 alembic sync 마이그레이션과 호환되지 않으므로 제거
_db_uri = settings.DATABASE_URI or ""
if "+asyncpg" in _db_uri:
    _db_uri = _db_uri.replace("+asyncpg", "")
config.set_main_option("sqlalchemy.url", _db_uri)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Base.metadata에 모든 모델의 메타데이터가 포함됨
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = _db_uri
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
