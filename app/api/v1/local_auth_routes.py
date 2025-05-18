from fastapi import APIRouter
from app.api.v1.endpoints.local_auth import router as local_auth_router

# 라우터 초기화
router = APIRouter()

# 로컬 인증 라우터 등록
router.include_router(
    local_auth_router,
    prefix="/local",
    tags=["로컬 인증"],
)