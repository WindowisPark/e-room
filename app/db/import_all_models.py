# app/db/import_all_models.py

# 기본 모델들 먼저 임포트
from app.models.user import User
from app.models.team import Team, TeamMember
from app.models.attendance import Attendance
from app.models.notification import Notification
from app.models.payment import Payment
from app.models.question import Question

# 중간 단계 모델 임포트
from app.models.tag import PDFFile, PDFTag, PDFTagMention

# 의존성이 높은 모델 마지막에 임포트
from app.models.task import Task
from app.models.team_activity import TeamActivity  # 있다면