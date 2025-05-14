# app/db/base.py
"""
이 파일은 애플리케이션 시작 시 SQLAlchemy를 초기화하는 데 사용됩니다.
"""

from app.db.base_class import Base  # noqa

# 모든 모델을 적절한 순서로 임포트
from app.db.import_all_models import *