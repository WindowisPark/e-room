# app/schemas/__init__.py
from .token import Token, TokenPayload
from .user import (
    User, 
    UserCreate,
    UserCreateOAuth,
    UserUpdate,
    UserInDB,
    UserProfileUpdate 
)

# 출석 스키마 추가
from .attendance import Attendance, AttendanceCreate

# 협업 기능을 위한 스키마 추가
from .team import TeamCreate, TeamUpdate, TeamResponse, TeamMemberCreate, TeamMemberResponse
from .tag import AnnotationCreate, AnnotationUpdate, AnnotationResponse, AnnotationList
from .notification import NotificationCreate, NotificationResponse

# 질문 스키마 추가
from .question import Question, QuestionCreate, QuestionBase