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

# 모든 모델 임포트 - 마이그레이션에 포함되도록
from app.models.user import User
# 기존 다른 모델들 임포트
# from app.models.payment import Payment  # 있다면 활성화

# 새로 추가한 협업 기능 모델 임포트
from app.models.team import Team, TeamMember
from app.models.tag import PDFFile, PDFTag, PDFTagMention
from app.models.notification import Notification
from app.models.attendance import Attendance 
from app.models.question import Question

config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URI)

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
    configuration["sqlalchemy.url"] = settings.DATABASE_URI
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