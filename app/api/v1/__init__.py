from fastapi import APIRouter

from app.api.v1 import auth
from app.api.v1.endpoints import (
    attendance, notifications, payments, question, tags, teams,
    phone_verification, team_pdf, team_activity, gamification, badges,
    user, events  # ✅ 추가
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["인증"])
api_router.include_router(user.router, prefix="/users", tags=["사용자 정보"])
api_router.include_router(phone_verification.router, prefix="/phone-verification", tags=["전화번호 인증"])
api_router.include_router(teams.router, prefix="/teams", tags=["팀 관리"])
api_router.include_router(team_pdf.router, prefix="/teams", tags=["팀 PDF 관리"])
api_router.include_router(team_activity.router, prefix="/teams", tags=["팀 활동 로그"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["알림"])
api_router.include_router(attendance.router, prefix="/attendance", tags=["출석"])
api_router.include_router(gamification.router, prefix="/gamification", tags=["게이미피케이션"])
api_router.include_router(badges.router, prefix="/gamification", tags=["배지"])
api_router.include_router(question.router, prefix="/questions", tags=["질문"])
api_router.include_router(tags.router, prefix="/tags", tags=["태그"])
api_router.include_router(payments.router, prefix="/payments", tags=["결제"])
api_router.include_router(events.router, prefix="/events", tags=["이벤트"])  # ✅ 다음 줄 추가!
