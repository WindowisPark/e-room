# app/db/base_models.py
"""
이 파일은 데이터베이스 모델들을 한 곳에 모아 Alembic이 자동으로 마이그레이션 할 수 있게 합니다.
실제 코드 실행 시에는 사용되지 않고, 마이그레이션 생성 시에만 사용됩니다.
"""

# SQLAlchemy Base 클래스
from app.db.base_class import Base

# 모든 모델 클래스 - 명시적 임포트
from app.models.user import User
from app.models.tag import PDFFile, PDFTag, PDFTagMention
from app.models.task import Task
from app.models.team import Team, TeamMember
from app.models.notification import Notification
from app.models.payment import Payment, PaymentStatus
from app.models.attendance import Attendance
from app.models.question import Question
from app.models.gamification import PointHistory, Badge, UserBadge, PointActionType, BadgeType