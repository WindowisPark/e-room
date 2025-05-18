# SQLAlchemy Base 클래스
from app.db.base_class import Base

# 가장 기본적인 독립 모델 먼저 임포트
from app.models.user import User
from app.models.notification import Notification
from app.models.payment import Payment, PaymentStatus
from app.models.attendance import Attendance
from app.models.question import Question
from app.models.gamification import PointHistory, Badge, UserBadge, PointActionType, BadgeType

# 상호 참조가 있는 모델들을 순서대로 임포트
from app.models.team import Team, TeamMember
from app.models.tag import PDFFile, PDFTag, PDFTagMention
from app.models.task import Task
from app.models.team_activity import TeamActivity