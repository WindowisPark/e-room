# app/services/session_manager.py (JSON 직렬화 문제 해결)

import json
import redis
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from app.core.config import settings
from app.services.persistent_chat_service import PersistentChatService
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)

class MessageEncoder(json.JSONEncoder):
    """LangChain 메시지 객체를 JSON으로 직렬화하는 인코더"""
    
    def default(self, obj):
        if isinstance(obj, BaseMessage):
            return {
                "type": obj.__class__.__name__,
                "content": obj.content,
                "additional_kwargs": getattr(obj, 'additional_kwargs', {}),
                "response_metadata": getattr(obj, 'response_metadata', {})
            }
        elif isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class MessageDecoder:
    """JSON에서 LangChain 메시지 객체로 역직렬화하는 디코더"""
    
    @staticmethod
    def decode_message(message_dict: Dict) -> BaseMessage:
        """메시지 딕셔너리를 LangChain 메시지 객체로 변환"""
        message_type = message_dict.get("type")
        content = message_dict.get("content", "")
        additional_kwargs = message_dict.get("additional_kwargs", {})
        
        if message_type == "HumanMessage":
            return HumanMessage(content=content, additional_kwargs=additional_kwargs)
        elif message_type == "AIMessage":
            return AIMessage(content=content, additional_kwargs=additional_kwargs)
        elif message_type == "SystemMessage":
            return SystemMessage(content=content, additional_kwargs=additional_kwargs)
        else:
            # 기본값으로 HumanMessage 반환
            return HumanMessage(content=content, additional_kwargs=additional_kwargs)
    
    @staticmethod
    def decode_messages(messages_list: List[Dict]) -> List[BaseMessage]:
        """메시지 리스트를 LangChain 메시지 객체 리스트로 변환"""
        if not messages_list:
            return []
        
        result = []
        for msg_dict in messages_list:
            if isinstance(msg_dict, dict) and "type" in msg_dict:
                result.append(MessageDecoder.decode_message(msg_dict))
            elif isinstance(msg_dict, BaseMessage):
                result.append(msg_dict)  # 이미 메시지 객체인 경우
        
        return result

class SessionManager:
    """Redis 기반 세션 관리자 (JSON 직렬화 지원)"""
    
    def __init__(self):
        # 메모리 캐시 (빠른 접근용)
        self.memory_sessions: Dict[str, Dict] = {}
        self.connection_ttl = 3600  # 1시간
      
    
    def _safe_serialize(self, data: Any) -> str:
        """안전한 JSON 직렬화 (LangChain 메시지 지원)"""
        try:
            return json.dumps(data, cls=MessageEncoder, ensure_ascii=False)
        except Exception as e:
            logger.error(f"JSON 직렬화 실패: {str(e)}")
            # 실패 시 기본 정보만 저장
            simplified_data = self._simplify_data(data)
            return json.dumps(simplified_data, ensure_ascii=False)
    
    def _safe_deserialize(self, data_str: str) -> Any:
        """안전한 JSON 역직렬화 (LangChain 메시지 지원)"""
        try:
            data = json.loads(data_str)
            return self._restore_messages(data)
        except Exception as e:
            logger.error(f"JSON 역직렬화 실패: {str(e)}")
            return {}
    
    def _simplify_data(self, data: Any) -> Any:
        """복잡한 객체를 단순한 형태로 변환"""
        if isinstance(data, dict):
            simplified = {}
            for key, value in data.items():
                try:
                    if isinstance(value, BaseMessage):
                        simplified[key] = {
                            "type": value.__class__.__name__,
                            "content": value.content
                        }
                    elif isinstance(value, list):
                        simplified[key] = [self._simplify_data(item) for item in value]
                    elif isinstance(value, dict):
                        simplified[key] = self._simplify_data(value)
                    else:
                        simplified[key] = value
                except:
                    simplified[key] = str(value)  # 최후의 수단
            return simplified
        elif isinstance(data, list):
            return [self._simplify_data(item) for item in data]
        elif isinstance(data, BaseMessage):
            return {
                "type": data.__class__.__name__,
                "content": data.content
            }
        else:
            return data
    
    def _restore_messages(self, data: Any) -> Any:
        """데이터에서 메시지 객체들을 복원"""
        if isinstance(data, dict):
            # messages 키가 있고 리스트인 경우 메시지 객체로 복원
            if "messages" in data and isinstance(data["messages"], list):
                data["messages"] = self.decoder.decode_messages(data["messages"])
            
            # agent_state 내부의 messages도 처리
            if "agent_state" in data and isinstance(data["agent_state"], dict):
                agent_state = data["agent_state"]
                if "messages" in agent_state and isinstance(agent_state["messages"], list):
                    agent_state["messages"] = self.decoder.decode_messages(agent_state["messages"])
            
            # 재귀적으로 다른 딕셔너리도 처리
            for key, value in data.items():
                if isinstance(value, dict):
                    data[key] = self._restore_messages(value)
        
        return data
    
    def create_session(self, user_id: str, task_type: str = "qa") -> str:
        """영구 세션 생성"""
        with SessionLocal() as db:
            session_id = PersistentChatService.create_session(db, int(user_id), task_type)
            
            # 메모리 캐시에도 저장
            self.memory_sessions[session_id] = {
                "user_id": user_id,
                "task_type": task_type,
                "created_at": datetime.now().isoformat(),
                "agent_state": {},
                "waiting_for": None,
                "current_request_type": None
            }
            
            return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """세션 조회 (메모리 우선, DB 백업)"""
        # 1. 메모리에서 먼저 찾기
        if session_id in self.memory_sessions:
            return self.memory_sessions[session_id]
        
        # 2. DB에서 찾아서 메모리에 로드
        with SessionLocal() as db:
            db_session = PersistentChatService.get_session(db, session_id)
            if db_session:
                session_data = {
                    "user_id": str(db_session.user_id),
                    "task_type": db_session.task_type,
                    "created_at": db_session.created_at.isoformat(),
                    "agent_state": db_session.agent_state or {},
                    "waiting_for": db_session.waiting_for,
                    "current_request_type": db_session.current_request_type
                }
                
                # 메모리에 캐시
                self.memory_sessions[session_id] = session_data
                return session_data
        
        return None
    
    def update_session(self, session_id: str, data: Dict[str, Any]) -> bool:
        """세션 업데이트 (메모리 + DB 동기화)"""
        # 1. 메모리 업데이트
        if session_id in self.memory_sessions:
            self.memory_sessions[session_id].update(data)
        
        # 2. DB 업데이트
        with SessionLocal() as db:
            PersistentChatService.update_session_state(db, session_id, data)
        
        return True
    
    def add_message_to_history(self, session_id: str, message, extra_data: Optional[Dict] = None):  # ✅ 수정
        """메시지 영구 저장"""
        with SessionLocal() as db:
            if hasattr(message, 'content'):
                message_type = "user" if "HumanMessage" in str(type(message)) else "ai"
                content = message.content
            else:
                message_type = "system"
                content = str(message)
            
            PersistentChatService.add_message(
                db, session_id, message_type, content, extra_data  # ✅ 수정
            )
    
    def add_message_to_history(self, session_id: str, message: BaseMessage) -> bool:
        """메시지 히스토리에 메시지 추가"""
        try:
            # 메시지를 직렬화 가능한 형태로 변환
            message_dict = {
                "type": message.__class__.__name__,
                "content": message.content,
                "timestamp": datetime.now().isoformat(),
                "additional_kwargs": getattr(message, 'additional_kwargs', {})
            }
            
            current_data = self.get_session(session_id)
            if not current_data:
                return False
            
            if "message_history" not in current_data:
                current_data["message_history"] = []
            
            current_data["message_history"].append(message_dict)
            
            # 메시지 히스토리 길이 제한 (최대 100개)
            if len(current_data["message_history"]) > 100:
                current_data["message_history"] = current_data["message_history"][-100:]
            
            return self.update_session(session_id, current_data)
            
        except Exception as e:
            logger.error(f"❌ 메시지 히스토리 추가 실패: {str(e)}")
            return False
    
    def get_chat_history(self, session_id: str) -> List[Dict]:
        """채팅 기록 조회"""
        with SessionLocal() as db:
            return PersistentChatService.get_chat_history(db, session_id)
    
    def cleanup_session(self, session_id: str) -> bool:
        """세션 삭제"""
        try:
            key = f"session:{session_id}"
            
            if self.redis_client:
                result = self.redis_client.delete(key)
                success = result > 0
            else:
                success = key in self.memory_store
                if success:
                    del self.memory_store[key]
            
            if success:
                logger.info(f"✅ 세션 삭제: {session_id}")
            else:
                logger.warning(f"⚠️ 삭제할 세션이 없음: {session_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ 세션 삭제 실패: {str(e)}")
            return False
    
    def extend_session_ttl(self, session_id: str, ttl: Optional[int] = None) -> bool:
        """세션 만료 시간 연장"""
        try:
            ttl = ttl or self.default_ttl
            key = f"session:{session_id}"
            
            if self.redis_client:
                result = self.redis_client.expire(key, ttl)
                return result
            else:
                if key in self.memory_store:
                    self.memory_store[key]["expires_at"] = datetime.now() + timedelta(seconds=ttl)
                    return True
                return False
                
        except Exception as e:
            logger.error(f"❌ 세션 TTL 연장 실패: {str(e)}")
            return False
    
    def get_user_chat_sessions(self, user_id: str, limit: int = 20) -> List[Dict]:
        """사용자 채팅 세션 목록"""
        with SessionLocal() as db:
            return PersistentChatService.get_user_sessions(db, int(user_id), limit)
    
    def get_session_stats(self, user_id: str) -> Dict:
        """사용자 세션 통계"""
        try:
            sessions = self.get_user_chat_sessions(user_id, limit=100)
            
            total_sessions = len(sessions)
            total_messages = sum(s.get("message_count", 0) for s in sessions)
            
            # 작업 타입별 통계
            task_stats = {}
            for session in sessions:
                task_type = session.get("task_type", "qa")
                task_stats[task_type] = task_stats.get(task_type, 0) + 1
            
            return {
                "total_sessions": total_sessions,
                "total_messages": total_messages,
                "task_type_stats": task_stats,
                "recent_sessions": sessions[:5]
            }
            
        except Exception as e:
            logger.error(f"❌ 세션 통계 조회 실패: {str(e)}")
            return {
                "total_sessions": 0,
                "total_messages": 0,
                "task_type_stats": {},
                "recent_sessions": []
            }