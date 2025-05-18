# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import auth
from app.core.config import settings
from app.api.v1.pdf_manager import router as pdf_router
from app.api.v1.admin import router as admin_router
from app.db.base import Base  # noqa

# 메인 API 라우터 추가
from app.api.v1 import api_router

# ✅ WebSocket 라우터 추가
from app.api.v1.websocket import ws_router

# ✅ 로컬 인증 라우터 추가
from app.api.v1.local_auth_routes import router as local_auth_router

# FastAPI 앱 초기화
app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Agent API with Authentication, PDF Management, and Team Collaboration",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
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

# ✅ 로컬 인증 라우터 추가
app.include_router(
    local_auth_router,
    prefix=f"{settings.API_V1_STR}/auth",
    tags=["Local Authentication"]
)

# PDF 관리 API 추가
app.include_router(
    pdf_router,
    prefix=f"{settings.API_V1_STR}/pdf",
    tags=["PDF Manager"]
)

# Admin 라우터
app.include_router(
    admin_router,
    prefix=f"{settings.API_V1_STR}/admin",
    tags=["Admin"]
)

# 메인 API 라우터 포함 (endpoints 폴더의 모든 API)
app.include_router(api_router, prefix=settings.API_V1_STR)

# ✅ WebSocket 라우터 포함
app.include_router(ws_router, prefix=f"{settings.API_V1_STR}/ws")

# 헬스 체크 엔드포인트
@app.get("/api/health", tags=["Health Check"])
def health_check():
    return {"status": "healthy"}

# Root 엔드포인트
@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to AI-Agent API with Team Collaboration",
        "docs_url": f"{settings.API_V1_STR}/docs",
        "openapi_url": f"{settings.API_V1_STR}/openapi.json"
    }

# ✅ Swagger에 JWT 인증 스키마 반영
from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="AI-Agent API with Authentication, PDF Management, and Team Collaboration",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    for path in openapi_schema["paths"].values():
        for operation in path.values():
            operation["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# ✅ 서버 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
