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

    def __init__(self, redis_url: str = settings.REDIS_URL):  # ✅ 수정된 부분
        self.redis_client = redis.from_url(redis_url, decode_responses=True)

    def _get_ttl(self, task_type: str) -> int:
        return self.QA_SESSION_TTL if task_type == "qa" else self.TASK_SESSION_TTL

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

        try:
            ttl = self._get_ttl(task_type)
            self.redis_client.setex(
                session_id,
                ttl,
                json.dumps(session_data, ensure_ascii=False)
            )
            if task_type == "qa":
                user_sessions_key = f"user_sessions:{user_id}"
                self.redis_client.lpush(user_sessions_key, session_id)
                self.redis_client.expire(user_sessions_key, self.QA_SESSION_TTL)
        except Exception as e:
            logger.warning(f"Redis 저장 실패, 인메모리 세션만 사용: {e}")

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
        try:
            data = self.redis_client.get(session_id)
            if data:
                session_data = json.loads(data)
                # TTL 갱신
                ttl = self._get_ttl(session_data.get("task_type", "qa"))
                self.redis_client.expire(session_id, ttl)
                return session_data
            return None
        except Exception as e:
            logger.error(f"세션 조회 실패: {session_id}, {str(e)}")
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
        try:
            current_data = self.get_session(session_id)
            if not current_data:
                return False
            
            # 기존 데이터와 병합
            current_data.update(data)
            current_data["last_activity"] = datetime.now().isoformat()
            
            # Redis에 저장
            ttl = self._get_ttl(current_data.get("task_type", "qa"))
            self.redis_client.setex(
                session_id,
                ttl,
                json.dumps(current_data, ensure_ascii=False)
            )

            return True
        except Exception as e:
            logger.error(f"세션 업데이트 실패: {session_id}, {str(e)}")
            return False
    
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
        try:
            user_sessions_key = f"user_sessions:{user_id}"
            session_ids = self.redis_client.lrange(user_sessions_key, 0, limit - 1)
            
            chat_sessions = []
            for session_id in session_ids:
                session_data = self.get_session(session_id)
                if session_data and session_data.get("task_type") == "qa":
                    # 채팅 목록용 요약 정보만 추출
                    chat_info = {
                        "session_id": session_id,
                        "title": session_data.get("chat_title", "새 채팅"),
                        "created_at": session_data.get("created_at"),
                        "last_activity": session_data.get("last_activity"),
                        "message_count": len(session_data.get("message_history", []))
                    }
                    chat_sessions.append(chat_info)
            
            # 최근 활동 순으로 정렬
            chat_sessions.sort(key=lambda x: x["last_activity"], reverse=True)
            return chat_sessions
            
        except Exception as e:
            logger.error(f"사용자 채팅 세션 조회 실패: {user_id}, {str(e)}")
            return []
    
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
        try:
            # 세션 데이터 조회
            session_data = self.get_session(session_id)
            if session_data:
                user_id = session_data.get("user_id")
                
                # 사용자 세션 목록에서 제거
                if user_id:
                    user_sessions_key = f"user_sessions:{user_id}"
                    self.redis_client.lrem(user_sessions_key, 0, session_id)
            
            # 세션 삭제
            self.redis_client.delete(session_id)
            logger.info(f"세션 정리 완료: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"세션 정리 실패: {session_id}, {str(e)}")
            return False
    
    def extend_session_ttl(self, session_id: str) -> bool:
        """
        세션 TTL 연장
        
        Args:
            session_id: 세션 ID
            
        Returns:
            성공 여부
        """
        try:
            session_data = self.get_session(session_id)
            if not session_data:
                return False
            ttl = self._get_ttl(session_data.get("task_type", "qa"))
            return self.redis_client.expire(session_id, ttl)
        except Exception as e:
            logger.error(f"세션 TTL 연장 실패: {session_id}, {str(e)}")
            return False
    
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
        try:
            user_sessions_key = f"user_sessions:{user_id}"
            total_sessions = self.redis_client.llen(user_sessions_key)
            
            # 활성 세션 수 계산
            active_sessions = 0
            session_ids = self.redis_client.lrange(user_sessions_key, 0, -1)
            for session_id in session_ids:
                if self.redis_client.exists(session_id):
                    active_sessions += 1
            
            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "user_id": user_id
            }
            
        except Exception as e:
            logger.error(f"세션 통계 조회 실패: {user_id}, {str(e)}")
            return {
                "total_sessions": 0,
                "active_sessions": 0,
                "user_id": user_id
            }