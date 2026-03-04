# app/api/v1/websocket/__init__.py

from fastapi import APIRouter
from .chat import router as chat_router

ws_router = APIRouter()
ws_router.include_router(chat_router, tags=["chat"])
