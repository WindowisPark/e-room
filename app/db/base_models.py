# app/db/base_models.py
from app.db.base_class import Base

# 모든 모델 클래스 명시적으로 임포트
from app.models.user import User
from app.models.attendance import Attendance
from app.models.question import Question
from app.models.notification import Notification
from app.models.payment import Payment
from app.models.tag import PDFTag, PDFTagMention # 실제 모델에 맞게 변경해야 합니다!!!!!!!!
from app.models.team import Team, TeamMember