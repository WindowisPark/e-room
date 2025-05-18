# app/db/base_models.py
"""
이 파일은 데이터베이스 모델들을 한 곳에 모아 Alembic이 자동으로 마이그레이션 할 수 있게 합니다.
실제 코드 실행 시에는 사용되지 않고, 마이그레이션 생성 시에만 사용됩니다.
"""

# SQLAlchemy Base 클래스
from app.db.base_class import Base

# 1. 기본적인 독립 모델 먼저 임포트 (다른 모델에 의존하지 않는 모델)
from app.models.gamification import PointHistory, Badge, UserBadge, PointActionType, BadgeType
from app.models.payment import Payment, PaymentStatus

# 2. 핵심 모델 - 다른 모델이 참조하는 기본 모델
from app.models.user import User

# 3. 2번 모델만 참조하는 모델
from app.models.attendance import Attendance
from app.models.notification import Notification
from app.models.question import Question
from app.models.team import Team, TeamMember

# 4. 여러 모델을 참조하는 복합 모델
from app.models.tag import PDFFile, PDFTag, PDFTagMention
from app.models.team_activity import TeamActivity

# 5. 가장 의존성이 많은 모델을 마지막에 임포트
from app.models.task import Task