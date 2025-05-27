# app/services/persistent_chat_service.py (새 파일)

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.chat import ChatSession, ChatMessage
from app.models.user import User
import uuid
import json
from datetime import datetime
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage


class PersistentChatService:
    """영구 채팅 세션 관리 서비스"""

    @staticmethod
    def _serialize_agent_state(state_data: Dict[str, Any]) -> Dict[str, Any]:
        """LangChain 메시지를 JSON 직렬화 가능한 형태로 변환"""
        if not state_data:
            return state_data
            
        # 깊은 복사로 원본 보존
        serialized_state = {}
        
        for key, value in state_data.items():
            if key == "messages" and isinstance(value, list):
                # LangChain 메시지들을 dict로 변환
                serialized_messages = []
                for msg in value:
                    if hasattr(msg, 'content') and hasattr(msg, '__class__'):
                        msg_dict = {
                            "type": msg.__class__.__name__,
                            "content": msg.content
                        }
                        # 추가 속성이 있다면 포함
                        if hasattr(msg, 'additional_kwargs'):
                            msg_dict["additional_kwargs"] = msg.additional_kwargs
                        serialized_messages.append(msg_dict)
                    else:
                        # 이미 dict 형태라면 그대로
                        serialized_messages.append(msg)
                serialized_state[key] = serialized_messages
            elif key == "agent_state":
                # 중첩된 agent_state 재귀 처리
                serialized_state[key] = PersistentChatService._serialize_agent_state(value)
            else:
                # 기본 직렬화 가능한 타입들
                try:
                    json.dumps(value)  # 직렬화 테스트
                    serialized_state[key] = value
                except (TypeError, ValueError):
                    # 직렬화 불가능한 객체는 문자열로 변환
                    serialized_state[key] = str(value)
        
        return serialized_state    
    
    def _deserialize_agent_state(state_data: Dict[str, Any]) -> Dict[str, Any]:
        """직렬화된 state를 LangChain 메시지로 복원"""
        if not state_data or "messages" not in state_data:
            return state_data
            
        deserialized_state = state_data.copy()
        
        if "messages" in state_data and isinstance(state_data["messages"], list):
            restored_messages = []
            for msg_dict in state_data["messages"]:
                if isinstance(msg_dict, dict) and "type" in msg_dict and "content" in msg_dict:
                    # dict에서 LangChain 메시지로 복원
                    msg_type = msg_dict["type"]
                    content = msg_dict["content"]
                    
                    if msg_type == "HumanMessage":
                        restored_messages.append(HumanMessage(content=content))
                    elif msg_type == "AIMessage":
                        restored_messages.append(AIMessage(content=content))
                    elif msg_type == "SystemMessage":
                        restored_messages.append(SystemMessage(content=content))
                    else:
                        # 알 수 없는 타입은 HumanMessage로 기본값
                        restored_messages.append(HumanMessage(content=content))
                else:
                    # 이미 메시지 객체거나 다른 형태
                    restored_messages.append(msg_dict)
            
            deserialized_state["messages"] = restored_messages
        
        return deserialized_state    
    
    @staticmethod
    def create_session(db: Session, user_id: int, task_type: str = "qa") -> str:
        """새 채팅 세션 생성"""
        session_id = f"{user_id}:{uuid.uuid4().hex[:8]}"
        
        db_session = ChatSession(
            session_id=session_id,
            user_id=user_id,
            task_type=task_type,
            title="새 채팅"  # 첫 메시지로 나중에 업데이트
        )
        
        db.add(db_session)
        db.commit()
        db.refresh(db_session)
        
        return session_id
    
    @staticmethod
    def get_session(db: Session, session_id: str) -> Optional[ChatSession]:
        """세션 조회 - 역직렬화 처리"""
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.is_active == True
        ).first()
        
        if session and session.agent_state:
            # 저장된 agent_state를 LangChain 메시지로 복원
            session.agent_state = PersistentChatService._deserialize_agent_state(
                session.agent_state
            )
        
        return session
    
    @staticmethod
    def update_session_title(db: Session, session_id: str, title: str):
        """세션 제목 업데이트 (첫 메시지 기반 자동 생성)"""
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if session:
            session.title = title[:50]  # 제목 길이 제한
            session.updated_at = datetime.utcnow()
            db.commit()
    
    @staticmethod
    def update_session_state(db: Session, session_id: str, state_data: Dict[str, Any]):
        """세션 상태 업데이트 - 직렬화 처리"""
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if session:
            # LangChain 메시지들을 직렬화
            serialized_agent_state = None
            if state_data.get("agent_state"):
                serialized_agent_state = PersistentChatService._serialize_agent_state(
                    state_data["agent_state"]
                )
            
            session.agent_state = serialized_agent_state
            session.waiting_for = state_data.get("waiting_for")
            session.current_request_type = state_data.get("current_request_type")
            session.task_type = state_data.get("task_type", session.task_type)
            session.updated_at = datetime.utcnow()
            db.commit()
    
    @staticmethod
    def add_message(
        db: Session, 
        session_id: str, 
        message_type: str, 
        content: str, 
        extra_data: Optional[Dict] = None  # ✅ metadata → extra_data
    ):
        """메시지 추가"""
        message = ChatMessage(
            session_id=session_id,
            message_type=message_type,
            content=content,
            extra_data=extra_data  # ✅ 수정
        )
        
        db.add(message)
        db.commit()
        
        # 첫 번째 사용자 메시지면 세션 제목 자동 생성
        if message_type == "user":
            messages_count = db.query(ChatMessage).filter(
                ChatMessage.session_id == session_id,
                ChatMessage.message_type == "user"
            ).count()
            
            if messages_count == 1:  # 첫 번째 사용자 메시지
                title = PersistentChatService._generate_title(content)
                PersistentChatService.update_session_title(db, session_id, title)
    
    @staticmethod
    def get_chat_history(db: Session, session_id: str) -> List[Dict]:
        """채팅 기록 조회"""
        messages = db.query(ChatMessage).filter(
            ChatMessage.session_id == session_id
        ).order_by(ChatMessage.created_at).all()
        
        return [
            {
                "id": msg.id,
                "type": msg.message_type,
                "content": msg.content,
                "extra_data": msg.extra_data,  # ✅ 수정
                "timestamp": msg.created_at.isoformat()
            }
            for msg in messages
        ]
    
    @staticmethod
    def get_user_sessions(
        db: Session, 
        user_id: int, 
        limit: int = 20, 
        offset: int = 0
    ) -> List[Dict]:
        """사용자의 모든 채팅 세션 목록"""
        sessions = db.query(ChatSession).filter(
            ChatSession.user_id == user_id,
            ChatSession.is_active == True
        ).order_by(ChatSession.updated_at.desc()).offset(offset).limit(limit).all()
        
        result = []
        for session in sessions:
            # 마지막 메시지 조회
            last_message = db.query(ChatMessage).filter(
                ChatMessage.session_id == session.session_id
            ).order_by(ChatMessage.created_at.desc()).first()
            
            result.append({
                "session_id": session.session_id,
                "title": session.title,
                "task_type": session.task_type,
                "created_at": session.created_at.isoformat(),
                "updated_at": session.updated_at.isoformat(),
                "last_message": last_message.content[:100] + "..." if last_message else "",
                "message_count": len(session.messages)
            })
        
        return result
    
    @staticmethod
    def delete_session(db: Session, session_id: str, user_id: int) -> bool:
        """세션 삭제 (soft delete)"""
        session = db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.user_id == user_id
        ).first()
        
        if session:
            session.is_active = False
            db.commit()
            return True
        return False
    
    @staticmethod
    def _generate_title(first_message: str) -> str:
        """첫 메시지 기반 제목 자동 생성"""
        # 간단한 제목 생성 로직
        if "요약" in first_message:
            return "📄 문서 요약"
        elif "시험" in first_message or "문제" in first_message:
            return "📝 시험 문제 생성"
        elif "계획" in first_message or "스케줄" in first_message:
            return "📅 학습 계획 수립"
        else:
            # 첫 15글자만 사용
            title = first_message.strip()[:15]
            return title if title else "새 채팅"