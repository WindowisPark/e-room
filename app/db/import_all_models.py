# app/db/import_all_models.py
"""
모델 간의 관계와 의존성을 명시적으로 관리하는 파일
SQLAlchemy와 Alembic에서 사용되며 순환 참조를 방지합니다.
"""

# 1. 사용자 모델
from app.models.user import User

# 2. PDF 관련 모델 (사용자 모델 의존)
from app.models.tag import PDFFile, PDFTag

# 3. 비밀번호 재설정 모델
from app.models.password_reset import PasswordResetToken

# 4. 취업 준비 모델
from app.models.resume import ResumeProfile, ResumeItem, ItemCategory
from app.models.job_research import SavedCompany
from app.models.cover_letter import CoverLetter, CoverLetterItem

# 5. 캘린더 모델
from app.models.calendar import CalendarTask, CalendarGoal


ALL_MODELS = [
    User,
    PDFFile, PDFTag,
    PasswordResetToken,
    ResumeProfile, ResumeItem,
    SavedCompany,
    CoverLetter, CoverLetterItem,
    CalendarTask, CalendarGoal,
]

__all__ = [
    'User',
    'PDFFile', 'PDFTag',
    'PasswordResetToken',
    'ResumeProfile', 'ResumeItem', 'ItemCategory',
    'SavedCompany',
    'CoverLetter', 'CoverLetterItem',
    'CalendarTask', 'CalendarGoal',
    'ALL_MODELS',
]
