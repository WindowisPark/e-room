# app/api/v1/__init__.py

from fastapi import APIRouter

from app.api.v1 import auth
from app.api.v1.endpoints import (
    attendance,
    notifications,
    payments,
    question,
    tags,
    teams
    # phone_verification 임포트 부분 제거
)

api_router = APIRouter()

# 인증 관련 라우터
api_router.include_router(auth.router, prefix="/auth", tags=["인증"])

# 전화번호 인증 라우터 제거
# api_router.include_router(
#     phone_verification.router, 
#     prefix="/phone-verification", 
#     tags=["전화번호 인증"]
# )

# 팀 관련 라우터
api_router.include_router(
    teams.router,
    prefix="/teams",
    tags=["팀 관리"]
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