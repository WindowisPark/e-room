# app/api/v1/websocket/__init__.py

from fastapi import APIRouter
from .collaboration import router as collaboration_router

ws_router = APIRouter()
ws_router.include_router(collaboration_router, tags=["websocket"])