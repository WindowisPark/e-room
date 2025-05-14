# app/db/base_models.py
from app.db.base_class import Base

# Task 모델을 가장 마지막에 임포트
from app.models.question import Question
from app.models.notification import Notification
from app.models.payment import Payment
from app.models.tag import PDFFile, PDFTag, PDFTagMention
from app.models.team import Team, TeamMember
from app.models.attendance import Attendance
from app.models.user import User
from app.models.task import Task  # Task 모델을 마지막에 임포트