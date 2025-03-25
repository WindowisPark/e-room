# app/core/websocket_manager.py
import json
from typing import Dict, List, Optional, Set
import redis.asyncio as redis
from fastapi import WebSocket, WebSocketDisconnect, Depends
from app.core.security import get_current_user_ws
from app.schemas.user import User

class ConnectionManager:
    """
    WebSocket 연결 및 방(팀스페이스) 관리 클래스
    """
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {}  # room_id -> {user_id: websocket}
        self.user_to_rooms: Dict[str, Set[str]] = {}  # user_id -> set of room_ids

    async def connect(self, websocket: WebSocket, room_id: str, user: User):
        """사용자를 특정 방에 연결"""
        await websocket.accept()
        
        # 방이 없으면 초기화
        if room_id not in self.active_connections:
            self.active_connections[room_id] = {}
        
        # 사용자를 방에 추가
        self.active_connections[room_id][str(user.id)] = websocket
        
        # 사용자가 속한 방 추적
        if str(user.id) not in self.user_to_rooms:
            self.user_to_rooms[str(user.id)] = set()
        self.user_to_rooms[str(user.id)].add(room_id)
        
        # Redis 채널 구독
        await self.redis.subscribe(f"room:{room_id}")
        
        # 사용자 입장 알림
        await self.broadcast_to_room(
            room_id, 
            {
                "type": "system", 
                "message": f"{user.username} 님이 입장했습니다", 
                "user_id": str(user.id)
            },
            exclude_user=None  # 모든 사용자에게 전송
        )

    async def disconnect(self, websocket: WebSocket, room_id: str, user: User):
        """사용자 연결 해제"""
        user_id = str(user.id)
        
        # 방에서 사용자 제거
        if room_id in self.active_connections and user_id in self.active_connections[room_id]:
            self.active_connections[room_id].pop(user_id)
            
            # 방이 비었다면 제거
            if not self.active_connections[room_id]:
                self.active_connections.pop(room_id)
            
            # 사용자의 방 추적 업데이트
            if user_id in self.user_to_rooms:
                self.user_to_rooms[user_id].discard(room_id)
                if not self.user_to_rooms[user_id]:
                    self.user_to_rooms.pop(user_id)
            
            # 방에 아무도 없다면 구독 해제
            if room_id not in self.active_connections:
                await self.redis.unsubscribe(f"room:{room_id}")
            
            # 퇴장 알림
            await self.broadcast_to_room(
                room_id, 
                {
                    "type": "system", 
                    "message": f"{user.username} 님이 퇴장했습니다", 
                    "user_id": user_id
                },
                exclude_user=user_id
            )

    async def send_personal_message(self, message: dict, user_id: str):
        """특정 사용자에게 개인 메시지 전송"""
        if user_id in self.user_to_rooms:
            for room_id in self.user_to_rooms[user_id]:
                if room_id in self.active_connections and user_id in self.active_connections[room_id]:
                    await self.active_connections[room_id][user_id].send_json(message)
        else:
            # 사용자가 WebSocket으로 연결되어 있지 않은 경우, Redis를 통해 접속 시 전달
            await self.redis.publish(f"user:{user_id}", json.dumps(message))

    async def broadcast_to_room(self, room_id: str, message: dict, exclude_user: Optional[str] = None):
        """방에 있는 모든 사용자에게 메시지 브로드캐스트"""
        if room_id in self.active_connections:
            for user_id, connection in self.active_connections[room_id].items():
                if exclude_user is None or user_id != exclude_user:
                    await connection.send_json(message)
        
        # 직접 연결되지 않은 클라이언트를 위해 Redis에도 발행
        await self.redis.publish(f"room:{room_id}", json.dumps({
            **message,
            "exclude_user": exclude_user
        }))

    async def listen_for_redis_messages(self):
        """Redis 메시지를 수신하여 WebSocket 클라이언트에 전달하는 백그라운드 작업"""
        pubsub = self.redis.pubsub()
        
        # 메시지 수신 처리
        async for message in pubsub.listen():
            if message["type"] == "message":
                channel = message["channel"].decode("utf-8")
                data = json.loads(message["data"].decode("utf-8"))
                
                # 방 브로드캐스트 처리
                if channel.startswith("room:"):
                    room_id = channel[5:]  # "room:" 접두사 제거
                    exclude_user = data.pop("exclude_user", None)
                    await self.broadcast_to_room(room_id, data, exclude_user)
                
                # 개인 메시지 처리
                elif channel.startswith("user:"):
                    user_id = channel[5:]  # "user:" 접두사 제거
                    await self.send_personal_message(data, user_id)