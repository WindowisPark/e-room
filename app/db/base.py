# app/db/base.py
from app.db.base_class import Base  # noqa

# 모든 모델 클래스 명시적으로 임포트
# 주의: 순환 참조 방지를 위해 SQLAlchemy 모델 초기화 시 모든 모델을 인식하도록 함
from app.models.user import User  # noqa
from app.models.attendance import Attendance  # noqa
from app.models.question import Question  # noqa
from app.models.notification import Notification  # noqa
from app.models.payment import Payment  # noqa
from app.models.tag import PDFTag, PDFTagMention  # noqa (이름은 실제 모델 이름으로 수정)
from app.models.team import Team, TeamMember  # noqa