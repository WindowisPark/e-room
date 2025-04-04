# app/db/base_models.py
from app.db.base_class import Base

# 모델 클래스 임포트 순서 조정
# Question을 먼저 임포트하고 User를 나중에 임포트
from app.models.question import Question
from app.models.notification import Notification
from app.models.payment import Payment
from app.models.tag import PDFTag, PDFTagMention
from app.models.team import Team, TeamMember
from app.models.attendance import Attendance
from app.models.user import User  # User를 가장 마지막에 임포트