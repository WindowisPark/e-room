# app/api/v1/__init__.py

from fastapi import APIRouter

from app.api.v1 import auth
# 개별 모듈 직접 임포트 (순환 참조 방지)
from app.api.v1.endpoints import attendance
from app.api.v1.endpoints import notifications
from app.api.v1.endpoints import payments
from app.api.v1.endpoints import question
from app.api.v1.endpoints import tags
from app.api.v1.endpoints import teams
from app.api.v1.endpoints import phone_verification
from app.api.v1.endpoints import team_pdf
from app.api.v1.endpoints import team_activity
from app.api.v1.endpoints import gamification
from app.api.v1.endpoints import badges
from app.api.v1.endpoints import pdf_agent  # 추가
from app.api.v1.endpoints import user  # 새로 추가한 user 엔드포인트 임포트

api_router = APIRouter()

# 인증 관련 라우터
api_router.include_router(auth.router, prefix="/auth", tags=["인증"])

# 사용자 관련 라우터 등록
api_router.include_router(
    user.router,
    prefix="/users",
    tags=["사용자 정보"]
)

# 전화번호 인증 라우터
api_router.include_router(
    phone_verification.router, 
    prefix="/phone-verification", 
    tags=["전화번호 인증"]
)

# PDF Agent 라우터 추가
api_router.include_router(
    pdf_agent.router,
    prefix="/pdf-agent",
    tags=["PDF Agent"]
)

# 팀 관련 라우터
api_router.include_router(
    teams.router,
    prefix="/teams",
    tags=["팀 관리"]
)

# 팀 PDF 관련 라우터
api_router.include_router(
    team_pdf.router,
    prefix="/teams",
    tags=["팀 PDF 관리"]
)

# ✅ 팀 활동 로그 관련 라우터 추가
api_router.include_router(
    team_activity.router,
    prefix="/teams",
    tags=["팀 활동 로그"]
)

# 알림 관련 라우터
api_router.include_router(
    notifications.router,
    prefix="/notifications",
    tags=["알림"]
)

# 출석 관련 라우터
api_router.include_router(
    attendance.router,
    prefix="/attendance",
    tags=["출석"]
)

api_router.include_router(
    gamification.router,
    prefix="/gamification",
    tags=["게이미피케이션"]
)

api_router.include_router(
    badges.router,
    prefix="/gamification",
    tags=["배지"]
)

# 질문 관련 라우터
api_router.include_router(
    question.router,
    prefix="/questions",
    tags=["질문"]
)

# 태그 관련 라우터
api_router.include_router(
    tags.router,
    prefix="/tags",
    tags=["태그"]
)

# 결제 관련 라우터
api_router.include_router(
    payments.router,
    prefix="/payments",
    tags=["결제"]
)