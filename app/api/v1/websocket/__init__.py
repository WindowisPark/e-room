# app/api/v1/websocket/__init__.py

from fastapi import APIRouter
from .collaboration import router as collaboration_router
from .chat import router as chat_router  # ✅ 추가

ws_router = APIRouter()
ws_router.include_router(collaboration_router, tags=["websocket"])
ws_router.include_router(chat_router, tags=["chat"])  # ✅ 추가
