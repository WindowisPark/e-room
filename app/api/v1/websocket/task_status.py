# app/api/v1/websocket/task_status.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
import asyncio
import json
import logging
from typing import Dict, Set, Any

from app.core.security import get_current_user_ws
from app.workers.task_manager import TaskManager

router = APIRouter()
logger = logging.getLogger(__name__)

# 클라이언트 연결 관리
class TaskStatusNotifier:
    """작업 상태 알림 관리 클래스"""

    # 연결된 클라이언트 저장: {job_id: {connection_id: WebSocket}}
    connected_clients: Dict[str, Dict[str, WebSocket]] = {}

    @classmethod
    async def connect(cls, websocket: WebSocket, job_id: str) -> str:
        """클라이언트 연결"""
        await websocket.accept()

        # 연결 ID 생성
        import uuid
        connection_id = str(uuid.uuid4())

        # 연결 정보 저장
        if job_id not in cls.connected_clients:
            cls.connected_clients[job_id] = {}

        cls.connected_clients[job_id][connection_id] = websocket

        return connection_id

    @classmethod
    async def disconnect(cls, job_id: str, connection_id: str) -> None:
        """클라이언트 연결 해제"""
        if job_id in cls.connected_clients:
            if connection_id in cls.connected_clients[job_id]:
                cls.connected_clients[job_id].pop(connection_id)

            # 해당 작업의 모든 연결이 종료되면 작업 항목도 제거
            if not cls.connected_clients[job_id]:
                cls.connected_clients.pop(job_id)

    @classmethod
    async def broadcast(cls, job_id: str, message: Dict[str, Any]) -> None:
        """모든 연결된 클라이언트에게 메시지 전송"""
        if job_id in cls.connected_clients:
            for websocket in cls.connected_clients[job_id].values():
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"메시지 전송 실패: {str(e)}")


@router.websocket("/tasks/{job_id}")
async def task_status_websocket(websocket: WebSocket, job_id: str):
    """작업 진행 상태 WebSocket 엔드포인트"""
    # 사용자 인증
    user = await get_current_user_ws(websocket)
    if not user:
        await websocket.close(code=1008, reason="인증 실패")
        return

    # 작업 소유자 확인 (실제 구현에서는 DB 조회 필요)
    if not job_id.endswith(f"_{user.id}"):
        await websocket.close(code=4003, reason="해당 작업에 접근할 권한이 없습니다")
        return

    # 클라이언트 연결
    connection_id = await TaskStatusNotifier.connect(websocket, job_id)

    # TaskManager 인스턴스
    task_manager = TaskManager()

    try:
        # 초기 상태 전송
        job_status = task_manager.get_job_status(job_id)
        await websocket.send_json({
            "type": "status_update",
            "job_id": job_id,
            "status": job_status.get("status", "unknown"),
            "progress": job_status.get("progress", 0),
            "result": job_status.get("result"),
            "message": "작업 상태 초기화"
        })

        # 주기적으로 작업 상태 확인 및 브로드캐스팅
        # 작업 완료 또는 실패 시 루프 종료
        while True:
            job_status = task_manager.get_job_status(job_id)
            status = job_status.get("status", "unknown")

            # 상태 업데이트 전송
            await websocket.send_json({
                "type": "status_update",
                "job_id": job_id,
                "status": status,
                "progress": job_status.get("progress", 0),
                "result": job_status.get("result"),
                "error": job_status.get("error"),
                "message": job_status.get("message", "작업 진행 중")
            })

            # 작업 완료 또는 실패 시 루프 종료
            if status in ["finished", "failed", "not_found"]:
                await websocket.send_json({
                    "type": "completed",
                    "job_id": job_id,
                    "status": status,
                    "result": job_status.get("result"),
                    "error": job_status.get("error"),
                    "message": "작업이 완료되었습니다"
                })
                break

            # 3초 대기 후 다음 업데이트
            await asyncio.sleep(3)

    except WebSocketDisconnect:
        logger.info(f"WebSocket 연결 종료: {job_id}, {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket 오류: {str(e)}")
    finally:
        # 연결 해제
        await TaskStatusNotifier.disconnect(job_id, connection_id)