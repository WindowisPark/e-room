# app/api/v1/__init__.py
from fastapi import APIRouter

# 기존 라우터들
from app.api.v1.endpoints.attendance import router as attendance_router
from app.api.v1.endpoints.payments import router as payments_router
from app.api.v1.endpoints.question import router as question_router
from app.api.v1.endpoints.teams import router as teams_router
from app.api.v1 import auth, admin

# 문제 해결을 위한 임시 라우터 생성
tags_router = APIRouter()
notifications_router = APIRouter()

@tags_router.get("/test")
def test_tags():
    return {"message": "Tags test"}

@notifications_router.get("/test")
def test_notifications():
    return {"message": "Notifications test"}

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(attendance_router, prefix="/attendance", tags=["attendance"])
api_router.include_router(payments_router, prefix="/payments", tags=["payments"])
api_router.include_router(question_router, prefix="/questions", tags=["questions"])
api_router.include_router(teams_router, prefix="/teams", tags=["teams"])
api_router.include_router(tags_router, prefix="/tags", tags=["tags"])
api_router.include_router(notifications_router, prefix="/notifications", tags=["notifications"])