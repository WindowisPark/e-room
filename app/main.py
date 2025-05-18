# ✅ app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi

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

@app.get("/api/health", tags=["Health Check"])
def health_check():
    return {"status": "healthy"}

@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to AI-Agent API with Team Collaboration",
        "docs_url": f"{settings.API_V1_STR}/docs",
        "openapi_url": f"{settings.API_V1_STR}/openapi.json"
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
        for operation in path_item.values():
            if not is_auth_exception:
                operation["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)