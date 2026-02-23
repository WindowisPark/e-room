from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.openapi.utils import get_openapi
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
_logger = logging.getLogger(__name__)

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

_static_dir = os.path.abspath(settings.STATIC_DIR)
if os.path.isdir(_static_dir):
    app.mount("/static", StaticFiles(directory=_static_dir, html=True), name="static")
else:
    _logger.warning(f"Static directory not found, skipping: {_static_dir}")

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(pdf_router, prefix=f"{settings.API_V1_STR}/pdf", tags=["PDF Manager"])
app.include_router(admin_router, prefix=f"{settings.API_V1_STR}/admin", tags=["Admin"])
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(ws_router, prefix=f"{settings.API_V1_STR}/ws")

if os.path.exists(f"{_static_dir}/assets"):
    app.mount("/assets", StaticFiles(directory=f"{_static_dir}/assets"), name="assets")
    _logger.info("/assets 경로 마운트 완료")


@app.get("/api/health", tags=["Health Check"])
def health_check():
    return {
        "status": "healthy",
        "static_directory": _static_dir,
        "index_html_exists": os.path.exists(f"{_static_dir}/index.html"),
        "assets_exists": os.path.exists(f"{_static_dir}/assets"),
        "static_files": os.listdir(_static_dir) if os.path.exists(_static_dir) else []
    }


@app.get("/api/debug/frontend")
def debug_frontend():
    return {
        "static_dir": _static_dir,
        "files_in_static": os.listdir(_static_dir) if os.path.exists(_static_dir) else [],
        "index_html_exists": os.path.exists(f"{_static_dir}/index.html"),
    }


@app.get("/{full_path:path}")
async def serve_spa(request: Request, full_path: str):
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="API endpoint not found")
    if full_path.startswith("assets/"):
        raise HTTPException(status_code=404, detail="Asset not found")
    file_path = os.path.join(_static_dir, full_path)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        return FileResponse(file_path)
    index_path = os.path.join(_static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "프론트엔드가 빌드되지 않았습니다"}


@app.get("/", include_in_schema=False)
def root():
    index_path = os.path.join(_static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "message": "AI-Agent API Server",
        "frontend_status": "Not built",
        "api_docs": f"{settings.API_V1_STR}/docs",
    }


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

    auth_exceptions = [
        f"{settings.API_V1_STR}/auth/register",
        f"{settings.API_V1_STR}/auth/login",
        f"{settings.API_V1_STR}/auth/token",
        f"{settings.API_V1_STR}/auth/kakao/authorize",
        f"{settings.API_V1_STR}/auth/kakao/callback",
        f"{settings.API_V1_STR}/auth/refresh-token",
    ]

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
