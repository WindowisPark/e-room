# app/services/session_manager.py (JSON 직렬화 문제 해결)

import json
import redis
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from app.core.config import settings

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
    
    def __init__(self, redis_url: str = settings.REDIS_URL, default_ttl: int = 3600):
        try:
            self.redis_client = redis.from_url(redis_url, decode_responses=True)
            self.redis_client.ping()  # 연결 테스트
            self.default_ttl = default_ttl
            self.encoder = MessageEncoder()
            self.decoder = MessageDecoder()
            logger.info("✅ Redis 연결 성공")
        except Exception as e:
            logger.warning(f"⚠️ Redis 연결 실패: {str(e)}, 메모리 기반으로 대체")
            self.redis_client = None
            self.memory_store = {}  # 메모리 기반 대체 저장소
            self.default_ttl = default_ttl
            self.encoder = MessageEncoder()
            self.decoder = MessageDecoder()
    
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
        """새 세션 생성"""
        session_id = f"{user_id}:{uuid.uuid4().hex[:8]}"
        
        session_data = {
            "session_id": session_id,
            "user_id": user_id,
            "task_type": task_type,
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "chat_title": "새 채팅",
            "message_history": [],
            "agent_state": {},
            "waiting_for": None,
            "current_request_type": None
        }
        
        key = f"session:{session_id}"
        
        try:
            serialized_data = self._safe_serialize(session_data)
            
            if self.redis_client:
                self.redis_client.setex(key, self.default_ttl, serialized_data)
            else:
                self.memory_store[key] = {
                    "data": serialized_data,
                    "expires_at": datetime.now() + timedelta(seconds=self.default_ttl)
                }
            
            logger.info(f"✅ 세션 생성: {session_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"❌ 세션 생성 실패: {str(e)}")
            raise
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """세션 데이터 조회"""
        key = f"session:{session_id}"
        
        try:
            if self.redis_client:
                data_str = self.redis_client.get(key)
                if data_str:
                    return self._safe_deserialize(data_str)
            else:
                if key in self.memory_store:
                    stored = self.memory_store[key]
                    if datetime.now() < stored["expires_at"]:
                        return self._safe_deserialize(stored["data"])
                    else:
                        del self.memory_store[key]  # 만료된 데이터 삭제
            
            return None
            
        except Exception as e:
            logger.error(f"❌ 세션 조회 실패: {str(e)}")
            return None
    
    def update_session(self, session_id: str, update_data: Dict) -> bool:
        """세션 데이터 업데이트"""
        try:
            current_data = self.get_session(session_id)
            if not current_data:
                logger.warning(f"⚠️ 세션을 찾을 수 없음: {session_id}")
                return False
            
            # 데이터 병합
            current_data.update(update_data)
            current_data["last_activity"] = datetime.now().isoformat()
            
            # 저장
            key = f"session:{session_id}"
            serialized_data = self._safe_serialize(current_data)
            
            if self.redis_client:
                self.redis_client.setex(key, self.default_ttl, serialized_data)
            else:
                self.memory_store[key] = {
                    "data": serialized_data,
                    "expires_at": datetime.now() + timedelta(seconds=self.default_ttl)
                }
            
            logger.debug(f"✅ 세션 업데이트: {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ 세션 업데이트 실패: {session_id}, {str(e)}")
            return False
    
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
        """채팅 히스토리 조회"""
        try:
            session_data = self.get_session(session_id)
            if session_data:
                return session_data.get("message_history", [])
            return []
        except Exception as e:
            logger.error(f"❌ 채팅 히스토리 조회 실패: {str(e)}")
            return []
    
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
        """사용자의 채팅 세션 목록 조회"""
        try:
            sessions = []
            pattern = f"session:{user_id}:*"
            
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                for key in keys[:limit]:
                    session_data = self.get_session(key.replace("session:", ""))
                    if session_data:
                        sessions.append({
                            "session_id": session_data.get("session_id"),
                            "title": session_data.get("chat_title", "새 채팅"),
                            "created_at": session_data.get("created_at"),
                            "last_activity": session_data.get("last_activity"),
                            "task_type": session_data.get("task_type", "qa"),
                            "message_count": len(session_data.get("message_history", []))
                        })
            else:
                # 메모리 스토어에서 검색
                for key, stored in self.memory_store.items():
                    if key.startswith(f"session:{user_id}:") and datetime.now() < stored["expires_at"]:
                        session_data = self._safe_deserialize(stored["data"])
                        if session_data:
                            sessions.append({
                                "session_id": session_data.get("session_id"),
                                "title": session_data.get("chat_title", "새 채팅"),
                                "created_at": session_data.get("created_at"),
                                "last_activity": session_data.get("last_activity"),
                                "task_type": session_data.get("task_type", "qa"),
                                "message_count": len(session_data.get("message_history", []))
                            })
            
            # 마지막 활동 시간 기준 정렬
            sessions.sort(key=lambda x: x.get("last_activity", ""), reverse=True)
            return sessions[:limit]
            
        except Exception as e:
            logger.error(f"❌ 사용자 세션 목록 조회 실패: {str(e)}")
            return []
    
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