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
# 사용자 관련
from app.models.user import User

# 팀/협업 관련
from app.models.team import Team, TeamMember
from app.models.team_activity import TeamActivity

# 문서/태그 관련
from app.models.tag import PDFFile, PDFTag, PDFTagMention

# 게이미피케이션 관련
from app.models.gamification import Badge, UserBadge, PointHistory
from app.models.attendance import Attendance

# 기타 기능 관련
from app.models.notification import Notification
from app.models.payment import Payment
from app.models.question import Question
from app.models.task import Task

# Alembic 설정
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