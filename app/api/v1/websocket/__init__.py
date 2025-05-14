# app/api/v1/websocket/__init__.py

from fastapi import APIRouter
from .collaboration import router as collaboration_router
from .task_status import router as task_status_router  # 작업 상태 라우터 추가

ws_router = APIRouter()
ws_router.include_router(collaboration_router, tags=["websocket"])
ws_router.include_router(task_status_router, tags=["websocket"])  # 작업 상태 라우터 등록