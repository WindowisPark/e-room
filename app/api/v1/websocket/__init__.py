# app/api/v1/websocket/__init__.py (완전 수정 버전)

from fastapi import APIRouter
from .collaboration import router as collaboration_router
from .chat import router as chat_router

# ✅ improved_chat 모듈 임포트 시도
try:
    from .improved_chat import router as improved_chat_router
    IMPROVED_CHAT_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ improved_chat 모듈 임포트 실패: {e}")
    IMPROVED_CHAT_AVAILABLE = False

ws_router = APIRouter()

# 기본 WebSocket 라우터들
ws_router.include_router(collaboration_router, tags=["websocket", "collaboration"])
ws_router.include_router(chat_router, tags=["websocket", "chat"])

# improved_chat이 사용 가능한 경우에만 포함
if IMPROVED_CHAT_AVAILABLE:
    ws_router.include_router(improved_chat_router, tags=["websocket", "improved-chat"])
    print("✅ improved_chat 라우터 등록됨")
else:
    print("❌ improved_chat 라우터 등록 실패")