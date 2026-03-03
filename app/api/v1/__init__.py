from fastapi import APIRouter

from app.api.v1 import auth
from app.api.v1.endpoints import (
    notifications, payments,
    phone_verification,
    pdf_agent, user,
    resume, job_research, cover_letter,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["인증"])
api_router.include_router(user.router, prefix="/users", tags=["사용자 정보"])
api_router.include_router(phone_verification.router, prefix="/phone-verification", tags=["전화번호 인증"])
api_router.include_router(pdf_agent.router, prefix="/pdf-agent", tags=["PDF Agent"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["알림"])
api_router.include_router(payments.router, prefix="/payments", tags=["결제"])
api_router.include_router(resume.router, prefix="/resume", tags=["이력서"])
api_router.include_router(job_research.router, prefix="/jobs", tags=["기업 조사"])
api_router.include_router(cover_letter.router, prefix="/coverletter", tags=["자소서"])
