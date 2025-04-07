# app/api/v1/websocket/__init__.py
from fastapi import APIRouter
from .collaboration import router as collaboration_router
from app.api.v1.websocket import collaboration

ws_router = APIRouter()
ws_router.include_router(collaboration.router, tags=["websocket"])