# app/services/persistent_chat_service.py (새 파일)

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.chat import ChatSession, ChatMessage
from app.models.user import User
import uuid
import json
from datetime import datetime

class PersistentChatService:
    """영구 채팅 세션 관리 서비스"""
    
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
        """세션 조회"""
        return db.query(ChatSession).filter(
            ChatSession.session_id == session_id,
            ChatSession.is_active == True
        ).first()
    
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
        """세션 상태 업데이트"""
        session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
        if session:
            session.agent_state = state_data.get("agent_state")
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