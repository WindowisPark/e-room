# app/db/import_all_models.py
"""
모델 간의 관계와 의존성을 명시적으로 관리하는 파일
SQLAlchemy와 Alembic에서 사용되며 순환 참조를 방지합니다.
"""

# 1. 기본 모델과 독립 모델 (다른 모델을 참조하지 않는 모델)
from app.models.gamification import PointHistory, Badge, UserBadge, PointActionType, BadgeType
from app.models.payment import Payment, PaymentStatus
from app.models.event import Event, UserEvent, InviteCode, EventType, EventStatus  # ✅ 이벤트 관련 추가

# 2. 사용자 모델 (다른 모델의 기반이 되는 모델)
from app.models.user import User

# 3. 사용자 관련 독립 모델
from app.models.attendance import Attendance
from app.models.notification import Notification
from app.models.question import Question

# 4. 팀 관련 모델 (사용자 모델 의존)
from app.models.team import Team, TeamMember
from app.models.team_activity import TeamActivity 

# 5. PDF 관련 모델 (사용자와 팀 모델 의존)
from app.models.tag import PDFFile, PDFTag, PDFTagMention

# 6. 비밀번호 재설정 모델
from app.models.password_reset import PasswordResetToken

# 7. 취업 준비 모델
from app.models.resume import ResumeProfile, ResumeItem, ItemCategory
from app.models.job_research import SavedCompany
from app.models.cover_letter import CoverLetter, CoverLetterItem


# 모든 모델을 모아서 리스트로 정의 (필요시 사용)
ALL_MODELS = [
    # 기본 모델
    PointHistory, Badge, UserBadge,
    Payment,

    # 이벤트 관련
    Event, UserEvent, InviteCode,

    # 사용자 모델
    User,

    # 사용자 관련 독립 모델
    Attendance, Notification, Question,

    # 팀 관련 모델
    Team, TeamMember, TeamActivity,

    # PDF 관련 모델
    PDFFile, PDFTag, PDFTagMention,

    # 비밀번호 재설정 모델
    PasswordResetToken,

    # 취업 준비 모델
    ResumeProfile, ResumeItem,
    SavedCompany,
    CoverLetter, CoverLetterItem,
]

# 마이그레이션에 필요한 모든 모델 의존성 제공
__all__ = [
    # 기본 모델과 열거형
    'PointHistory', 'Badge', 'UserBadge', 'PointActionType', 'BadgeType',
    'Payment', 'PaymentStatus',

    # 이벤트 관련
    'Event', 'UserEvent', 'InviteCode', 'EventType', 'EventStatus',

    # 사용자 모델
    'User',

    # 독립 모델
    'Attendance', 'Notification', 'Question',

    # 팀 관련 모델
    'Team', 'TeamMember', 'TeamActivity',

    # PDF 관련 모델
    'PDFFile', 'PDFTag', 'PDFTagMention',

    # 비밀번호 재설정 모델
    'PasswordResetToken',

    # 취업 준비 모델
    'ResumeProfile', 'ResumeItem', 'ItemCategory',
    'SavedCompany',
    'CoverLetter', 'CoverLetterItem',

    # 모델 컬렉션
    'ALL_MODELS'
]
