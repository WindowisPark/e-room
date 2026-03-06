# app/services/session_manager.py

import redis
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
import logging
from app.core.config import settings  # 추가

logger = logging.getLogger(__name__)



class SessionManager:
    QA_SESSION_TTL = 3600 * 24 * 30   # QA 채팅 이력 30일 보존
    TASK_SESSION_TTL = 3600 * 2        # summary/exam/schedule은 2시간 유지

    def __init__(self, redis_url: str = settings.REDIS_URL):
        self.redis_client = redis.from_url(redis_url, decode_responses=True)
        # Redis 불가 시 인메모리 폴백 (로컬 개발용 — 서버 재시작 시 소실)
        self._memory: dict = {}
        self._memory_user_sessions: dict = {}

    # ── 내부 헬퍼: Redis 우선, 실패 시 인메모리 ────────────────────────────────

    def _store(self, key: str, value: str) -> None:
        try:
            ttl = self.QA_SESSION_TTL
            self.redis_client.setex(key, ttl, value)
        except Exception:
            self._memory[key] = value

    def _fetch(self, key: str) -> str | None:
        try:
            return self.redis_client.get(key)
        except Exception:
            return self._memory.get(key)

    def _remove(self, key: str) -> None:
        try:
            self.redis_client.delete(key)
        except Exception:
            self._memory.pop(key, None)

    def _expire(self, key: str, ttl: int) -> None:
        try:
            self.redis_client.expire(key, ttl)
        except Exception:
            pass  # 인메모리는 TTL 불필요

    def _lpush(self, key: str, value: str) -> None:
        try:
            self.redis_client.lpush(key, value)
            self.redis_client.expire(key, self.QA_SESSION_TTL)
        except Exception:
            self._memory_user_sessions.setdefault(key, []).insert(0, value)

    def _lrange(self, key: str, start: int, end: int) -> list:
        try:
            return self.redis_client.lrange(key, start, end)
        except Exception:
            items = self._memory_user_sessions.get(key, [])
            return items[start: None if end == -1 else end + 1]

    def _lrem(self, key: str, value: str) -> None:
        try:
            self.redis_client.lrem(key, 0, value)
        except Exception:
            lst = self._memory_user_sessions.get(key, [])
            self._memory_user_sessions[key] = [v for v in lst if v != value]

    def _llen(self, key: str) -> int:
        try:
            return self.redis_client.llen(key)
        except Exception:
            return len(self._memory_user_sessions.get(key, []))

    def _exists(self, key: str) -> bool:
        try:
            return bool(self.redis_client.exists(key))
        except Exception:
            return key in self._memory

    def _get_ttl(self, task_type: str) -> int:
        return self.QA_SESSION_TTL if task_type in ("qa", "qa_system") else self.TASK_SESSION_TTL

    def create_session(self, user_id: str, task_type: str = None) -> str:
        """
        새 세션 생성

        Args:
            user_id: 사용자 ID
            task_type: 작업 타입 (qa, summary, exam, scheduler)

        Returns:
            session_id: 생성된 세션 ID
        """
        session_id = f"session:{user_id}:{uuid.uuid4().hex[:8]}"

        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "task_type": task_type,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "agent_state": {},
            "waiting_for": None,
            "chat_title": None,
            "message_history": [],
            "current_request_type": None,
            "selected_files": [],
            "processing_status": "idle"
        }

        self._store(session_id, json.dumps(session_data, ensure_ascii=False))
        if task_type == "qa":
            self._lpush(f"user_sessions:{user_id}", session_id)

        logger.info(f"새 세션 생성: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        세션 데이터 조회
        
        Args:
            session_id: 세션 ID
            
        Returns:
            세션 데이터 또는 None
        """
        data = self._fetch(session_id)
        if data:
            session_data = json.loads(data)
            ttl = self._get_ttl(session_data.get("task_type", "qa"))
            self._expire(session_id, ttl)
            return session_data
        return None
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """
        세션 데이터 업데이트
        
        Args:
            session_id: 세션 ID
            data: 업데이트할 데이터
            
        Returns:
            성공 여부
        """
        current_data = self.get_session(session_id)
        if not current_data:
            return False
        current_data.update(data)
        current_data["last_activity"] = datetime.now().isoformat()
        self._store(session_id, json.dumps(current_data, ensure_ascii=False))
        return True
    
    def add_message_to_history(self, session_id: str, message: BaseMessage) -> bool:
        """
        QA 대화 히스토리에 메시지 추가
        
        Args:
            session_id: 세션 ID
            message: 추가할 메시지
            
        Returns:
            성공 여부
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                return False
            
            # 히스토리에 추가
            if "message_history" not in session_data:
                session_data["message_history"] = []

            message_dict = {
                "type": message.__class__.__name__,
                "content": message.content,
                "timestamp": datetime.now().isoformat()
            }
            session_data["message_history"].append(message_dict)

            # 히스토리 길이 제한 (최근 50개만 유지)
            if len(session_data["message_history"]) > 50:
                session_data["message_history"] = session_data["message_history"][-50:]

            # 첫 번째 사용자 메시지면 채팅 제목 생성
            if (session_data.get("chat_title") is None and
                isinstance(message, HumanMessage) and
                len(session_data["message_history"]) == 1):

                title = self.generate_chat_title(message.content)
                session_data["chat_title"] = title
            
            return self.update_session(session_id, session_data)
            
        except Exception as e:
            logger.error(f"메시지 히스토리 추가 실패: {session_id}, {str(e)}")
            return False
    
    def generate_chat_title(self, first_message: str) -> str:
        """
        첫 메시지를 바탕으로 채팅 제목 생성
        
        Args:
            first_message: 첫 번째 사용자 메시지
            
        Returns:
            생성된 제목
        """
        # 간단한 제목 생성 로직 (추후 LLM으로 개선 가능)
        title = first_message[:30].strip()
        if len(first_message) > 30:
            title += "..."
        
        # 특수문자 제거
        import re
        title = re.sub(r'[^\w\s가-힣]', '', title)
        
        return title or "새 채팅"
    
    def get_user_chat_sessions(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        사용자의 QA 채팅 세션 목록 조회
        
        Args:
            user_id: 사용자 ID
            limit: 최대 조회 개수
            
        Returns:
            채팅 세션 목록
        """
        user_sessions_key = f"user_sessions:{user_id}"
        session_ids = self._lrange(user_sessions_key, 0, limit - 1)

        chat_sessions = []
        for session_id in session_ids:
            session_data = self.get_session(session_id)
            if session_data and session_data.get("task_type") in ("qa", "qa_system"):
                chat_sessions.append({
                    "session_id": session_id,
                    "title": session_data.get("chat_title", "새 채팅"),
                    "created_at": session_data.get("created_at"),
                    "last_activity": session_data.get("last_activity"),
                    "message_count": len(session_data.get("message_history", []))
                })

        chat_sessions.sort(key=lambda x: x["last_activity"], reverse=True)
        return chat_sessions
    
    def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """
        특정 채팅의 메시지 히스토리 조회
        
        Args:
            session_id: 세션 ID
            
        Returns:
            메시지 히스토리
        """
        try:
            session_data = self.get_session(session_id)
            if session_data:
                return session_data.get("message_history", [])
            return []
        except Exception as e:
            logger.error(f"채팅 히스토리 조회 실패: {session_id}, {str(e)}")
            return []
    
    def cleanup_session(self, session_id: str) -> bool:
        """
        세션 정리
        
        Args:
            session_id: 세션 ID
            
        Returns:
            성공 여부
        """
        session_data = self.get_session(session_id)
        if session_data:
            user_id = session_data.get("user_id")
            if user_id:
                self._lrem(f"user_sessions:{user_id}", session_id)
        self._remove(session_id)
        logger.info(f"세션 정리 완료: {session_id}")
        return True
    
    def extend_session_ttl(self, session_id: str) -> bool:
        """
        세션 TTL 연장
        
        Args:
            session_id: 세션 ID
            
        Returns:
            성공 여부
        """
        session_data = self.get_session(session_id)
        if not session_data:
            return False
        ttl = self._get_ttl(session_data.get("task_type", "qa"))
        self._expire(session_id, ttl)
        return True
    
    def cleanup_expired_sessions(self):
        """
        만료된 세션들 정리 (백그라운드 작업용)
        """
        try:
            # 만료된 세션들은 Redis TTL에 의해 자동 삭제됨
            # 필요시 추가 정리 로직 구현
            logger.info("만료된 세션 정리 완료")
        except Exception as e:
            logger.error(f"세션 정리 중 오류: {str(e)}")
    
    def get_session_stats(self, user_id: str) -> Dict[str, Any]:
        """
        사용자 세션 통계 조회
        
        Args:
            user_id: 사용자 ID
            
        Returns:
            세션 통계
        """
        user_sessions_key = f"user_sessions:{user_id}"
        total_sessions = self._llen(user_sessions_key)
        session_ids = self._lrange(user_sessions_key, 0, -1)
        active_sessions = sum(1 for sid in session_ids if self._exists(sid))
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "user_id": user_id
        }