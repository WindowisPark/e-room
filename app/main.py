# app/main.py - planova_web 프로젝트 전용 수정

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.openapi.utils import get_openapi
import os
import logging
from fastapi import HTTPException
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from app.core.config import settings
from app.api.v1.pdf_manager import router as pdf_router
from app.api.v1.admin import router as admin_router
from app.api.v1 import api_router
from app.api.v1.websocket import ws_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AI-Agent API with Authentication, PDF Management, and Team Collaboration",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc"
)

# ✅ planova_web 빌드 결과물 경로 설정
STATIC_DIR = "./static"  # planova_web/dist 내용이 복사된 폴더

# 정적 디렉토리 확인 및 생성
if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
    logger.warning(f"정적 디렉토리가 없어서 생성했습니다: {STATIC_DIR}")
    logger.warning("planova_web 프론트엔드를 빌드하고 static 폴더로 복사하세요")

# CORS 설정
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# ✅ API 라우터 등록 (우선순위)
app.include_router(pdf_router, prefix=f"{settings.API_V1_STR}/pdf", tags=["PDF Manager"])
app.include_router(admin_router, prefix=f"{settings.API_V1_STR}/admin", tags=["Admin"])
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(ws_router, prefix=f"{settings.API_V1_STR}/ws")

# ✅ 정적 파일 서빙 (Vite 빌드 결과물)
# assets 폴더 (JS, CSS, 이미지 등)
if os.path.exists(f"{STATIC_DIR}/assets"):
    app.mount("/assets", StaticFiles(directory=f"{STATIC_DIR}/assets"), name="assets")
    logger.info("✅ /assets 경로 마운트 완료")

# ✅ API 헬스체크 및 디버깅
@app.get("/api/health", tags=["Health Check"])
def health_check():
    index_exists = os.path.exists(f"{STATIC_DIR}/index.html")
    assets_exists = os.path.exists(f"{STATIC_DIR}/assets")
    
    return {
        "status": "healthy",
        "static_directory": STATIC_DIR,
        "index_html_exists": index_exists,
        "assets_exists": assets_exists,
        "static_files": os.listdir(STATIC_DIR) if os.path.exists(STATIC_DIR) else []
    }

# ✅ 개발용 디버깅 엔드포인트
@app.get("/api/debug/frontend")
def debug_frontend():
    return {
        "static_dir": STATIC_DIR,
        "files_in_static": os.listdir(STATIC_DIR) if os.path.exists(STATIC_DIR) else [],
        "index_html_exists": os.path.exists(f"{STATIC_DIR}/index.html"),
        "build_instructions": [
            "1. cd planova_web",
            "2. npm install",
            "3. npm run build", 
            "4. cd ..",
            "5. Copy-Item -Recurse planova_web\\dist\\* static\\ -Force"
        ]
    }

# 기존 serve_spa 함수 전체를 이것으로 교체
@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    # API 경로는 제외
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    
    # assets 폴더는 이미 마운트되어 있으므로 여기서 처리하지 않음
    if full_path.startswith("assets/"):
        raise HTTPException(status_code=404, detail="Asset not found")
    
    # 기타 정적 파일들
    file_path = os.path.join(STATIC_DIR, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # SPA 라우팅: 모든 경로를 index.html로
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    else:
        return {"message": "프론트엔드가 빌드되지 않았습니다"}

# ✅ 루트 경로
@app.get("/", include_in_schema=False)
def root():
    """루트 경로 - 프론트엔드 또는 API 정보"""
    index_path = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    
    return {
        "message": "AI-Agent API Server",
        "frontend_status": "Not built",
        "api_docs": f"{settings.API_V1_STR}/docs",
        "build_frontend": "cd planova_web && npm run build"
    }

# OpenAPI 스키마 설정
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=settings.PROJECT_NAME,
        version="1.0.0",
        description="AI-Agent API with Authentication, PDF Management, and Team Collaboration",
        routes=app.routes,
    )

    # JWT 인증 스키마 추가
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }

    # 인증이 필요 없는 경로들
    auth_exceptions = [
        f"{settings.API_V1_STR}/auth/register",
        f"{settings.API_V1_STR}/auth/login",
        f"{settings.API_V1_STR}/auth/token",
        f"{settings.API_V1_STR}/auth/kakao/authorize",
        f"{settings.API_V1_STR}/auth/kakao/callback",
        f"{settings.API_V1_STR}/auth/refresh-token",
    ]

    # 나머지 경로에 인증 적용
    for path, path_item in openapi_schema["paths"].items():
        is_auth_exception = any(path.startswith(exc) for exc in auth_exceptions)
        if not is_auth_exception:
            for operation in path_item.values():
                if isinstance(operation, dict):
                    operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)