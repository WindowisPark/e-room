# app/api/v1/websocket/collaboration.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
import json
import logging
import asyncio
from typing import Dict, Any

from app.db.session import get_db
from app.core.security import get_current_user_ws
from app.core.redis_helper import (
    publish_message, subscribe_channel, get_channel_messages,
    add_user_to_team_presence, remove_user_from_team_presence,
    store_cursor_position, get_team_presence, get_all_cursor_positions
)
from app.crud.crud_team import check_user_in_team
from app.models.user import User
from app.schemas.collaboration import (
    CursorUpdateMessage,
    AnnotationCreateMessage,
    AnnotationUpdateMessage,
    AnnotationDeleteMessage,
    UserPresenceMessage,
    CollaborationMessageBase
)
from app.services.team_activity_service import log_team_activity

message_type_map = {
    "cursor_update": CursorUpdateMessage,
    "annotation_create": AnnotationCreateMessage,
    "annotation_update": AnnotationUpdateMessage,
    "annotation_delete": AnnotationDeleteMessage,
    "user_presence": UserPresenceMessage,
}

router = APIRouter()
logger = logging.getLogger(__name__)

@router.websocket("/team/{team_id}/collaborate")
async def team_collaboration(
    websocket: WebSocket,
    team_id: int
):
    # 사용자 인증
    user = await get_current_user_ws(websocket)
    if not user:
        await websocket.close(code=1008, reason="인증 실패")
        return

    # DB 세션 및 팀 멤버 확인
    db: Session = next(get_db())
    if not check_user_in_team(db, team_id=team_id, user_id=user.id):
        await websocket.close(code=4003, reason="팀에 속하지 않은 사용자입니다")
        return

    await websocket.accept()

    # Redis Presence 등록 (TTL 300초)
    await add_user_to_team_presence(str(team_id), str(user.id), 300)

    channel = f"team:{team_id}"
    pubsub = await subscribe_channel(channel)

    # 참여자 전체 목록 전송
    presence = await get_team_presence(str(team_id))
    await websocket.send_json({
        "type": "presence_update",
        "team_id": team_id,
        "users": presence
    })

    # 커서 위치 전체 전송
    cursors = await get_all_cursor_positions(str(team_id), "*")
    await websocket.send_json({
        "type": "cursor_positions",
        "positions": cursors
    })

    # 입장 브로드캐스트
    await publish_message(channel, {
        "type": "user_joined",
        "user_id": user.id,
        "username": user.username
    })

    try:
        # Redis 메시지 백그라운드 수신
        redis_task = asyncio.create_task(
            handle_redis_messages(pubsub, websocket, user.id)
        )

        # 클라이언트 메시지 수신 루프
        while True:
            data = await websocket.receive_text()
            await process_client_message(data, team_id, user)

    except WebSocketDisconnect:
        logger.info(f"WebSocket 종료: User ID {user.id}, Team ID {team_id}")
    except Exception as e:
        logger.error(f"WebSocket 예외: {str(e)}")
    finally:
        if 'redis_task' in locals():
            redis_task.cancel()
        await remove_user_from_team_presence(str(team_id), str(user.id))
        await publish_message(channel, {
            "type": "user_left",
            "user_id": user.id,
            "username": user.username
        })


async def handle_redis_messages(pubsub, websocket: WebSocket, user_id: int):
    """Redis 채널에서 수신한 메시지를 클라이언트에 전달"""
    async for message in get_channel_messages(pubsub):
        if message.get("sender_id") == user_id:
            continue
        await websocket.send_json(message)


async def process_client_message(data: str, team_id: int, user: User):
    """WebSocket 메시지를 받아 파싱, Redis 브로드캐스트, 활동 로그 저장"""
    try:
        json_data = json.loads(data)
        msg_type = json_data.get("type")

        schema_cls = message_type_map.get(msg_type)
        if not schema_cls:
            logger.warning(f"알 수 없는 메시지 타입: {msg_type}")
            return

        # 기본 필드 추가
        json_data.update({
            "sender_id": user.id,
            "sender_name": user.username,
            "team_id": team_id
        })

        # 메시지 파싱
        message_obj = schema_cls(**json_data)

        # 특정 메시지의 부가 처리
        if isinstance(message_obj, CursorUpdateMessage):
            cursor = message_obj.data
            await store_cursor_position(
                str(team_id),
                str(user.id),
                str(cursor.pdf_id),
                cursor.page,
                {"x": cursor.x, "y": cursor.y}
            )

        # ✅ 활동 로그 기록 (필요한 타입만)
        if isinstance(message_obj, (AnnotationCreateMessage, AnnotationUpdateMessage, AnnotationDeleteMessage)):
            action_map = {
                "annotation_create": "create",
                "annotation_update": "update",
                "annotation_delete": "delete"
            }
            await log_team_activity(
                db=next(get_db()),
                team_id=team_id,
                user_id=user.id,
                action=action_map.get(message_obj.type, "update"),
                resource_type="annotation",
                resource_id=None,  # 추후 주석 ID 연동 시 확장
                details=message_obj.data
            )

        # 메시지 브로드캐스트
        await publish_message(f"team:{team_id}", message_obj.dict())

    except json.JSONDecodeError:
        logger.error(f"[WebSocket] 잘못된 JSON 형식: {data}")
    except Exception as e:
        logger.error(f"[WebSocket] 메시지 처리 오류: {str(e)}")


async def handle_cursor_move(message: Dict[str, Any], team_id: int, user: User):
    """커서 위치 업데이트 처리"""
    pdf_id = message.get("pdf_id")
    page = message.get("page")
    position = message.get("position")
    if pdf_id and page is not None and position:
        await store_cursor_position(
            str(team_id),
            str(user.id),
            str(pdf_id),
            page,
            position
        )


async def handle_highlight(message: Dict[str, Any], team_id: int, user: User):
    """하이라이트 처리 (단순 브로드캐스트용)"""
    # 필요한 필드: pdf_id, page, start, end, color
    required = ("pdf_id", "page", "start", "end", "color")
    if not all(k in message for k in required):
        logger.warning("하이라이트 필드 누락")
        return


async def handle_comment(message: Dict[str, Any], team_id: int, user: User):
    """댓글 처리 (위치 + 텍스트 포함)"""
    required = ("pdf_id", "page", "position", "text")
    if not all(k in message for k in required):
        logger.warning("댓글 필드 누락")
        return
