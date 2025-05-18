# app/db/import_all_models.py

# gamification 모델을 가장 먼저 임포트
from app.models.gamification import PointHistory, Badge, UserBadge, PointActionType, BadgeType

# TeamActivity 모델을 먼저 임포트 (순환 참조 방지)
from app.models.team_activity import TeamActivity

# 기본 모델들 임포트
from app.models.attendance import Attendance
from app.models.notification import Notification
from app.models.payment import Payment
from app.models.question import Question

# 중간 단계 모델 임포트
from app.models.tag import PDFFile, PDFTag, PDFTagMention
from app.models.team import Team, TeamMember

# 의존성이 있는 사용자 모델
from app.models.user import User

# 의존성이 높은 모델 마지막에 임포트
from app.models.task import Task