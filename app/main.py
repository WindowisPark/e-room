# ai-agent/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth
from app.core.config import settings
from app.api.v1.pdf_manager import router as pdf_router
from app.api.v1.admin import router as admin_router

# FastAPI 앱 초기화
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Agent API with Authentication and PDF Management",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=None
)

# CORS 미들웨어 설정
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# API 라우터 포함
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["Authentication"]
)

# PDF 관리 API 추가
app.include_router(
    pdf_router,
    prefix=f"{settings.API_V1_STR}/pdf",
    tags=["PDF Manager"]
)

# ✅ `admin` API 라우터 포함
app.include_router(
    admin_router,
    prefix=f"{settings.API_V1_STR}/admin",
    tags=["Admin"]
)

# 헬스 체크 엔드포인트
@app.get("/health", tags=["Health Check"])
def health_check():
    return {"status": "healthy"}

# Root 엔드포인트
@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to AI-Agent API",
        "docs_url": f"{settings.API_V1_STR}/docs",
        "openapi_url": f"{settings.API_V1_STR}/openapi.json"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
