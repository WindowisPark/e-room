# app/api/v1/__init__.py

from fastapi import APIRouter

# 통합 인증
from app.api.v1 import auth

# 각 도메인별 엔드포인트
from app.api.v1.endpoints import (
    attendance,
    notifications,
    payments,
    question,
    tags,
    teams,
    phone_verification,
    team_pdf,
    team_activity,
    gamification,
    badges,
    pdf_agent,
    user,
    local_auth  # ✅ 중요: 로컬 인증 포함
)

api_router = APIRouter()

# ✅ 인증 관련 라우터 (카카오, refresh, me, logout 등)
api_router.include_router(auth.router, prefix="/auth", tags=["인증"])

# ✅ 로컬 인증 라우터 명시적으로 Swagger에 등록
api_router.include_router(local_auth.router, prefix="/auth/local", tags=["로컬 인증"])

# ✅ 기타 도메인 라우터들
api_router.include_router(user.router, prefix="/users", tags=["사용자 정보"])
api_router.include_router(phone_verification.router, prefix="/phone-verification", tags=["전화번호 인증"])
api_router.include_router(pdf_agent.router, prefix="/pdf-agent", tags=["PDF Agent"])
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
