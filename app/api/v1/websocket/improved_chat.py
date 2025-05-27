# app/api/v1/websocket/improved_chat.py
"""
기존 chat.py를 개선한 버전
WebSocket 어댑터 패턴을 활용하여 Graph/Node와 연결
"""

import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session

from app.services.session_manager import SessionManager
from app.services.pdf_agent.tools import get_initial_state
from app.services.pdf_agent.adapters.websocket_adapter import WebSocketNodeAdapter
from app.api import deps
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

class ImprovedWebSocketManager:
    """어댑터 패턴을 활용한 개선된 WebSocket 매니저"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_manager = SessionManager()
        self.adapter = WebSocketNodeAdapter(self)
    
    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """WebSocket 연결 및 세션 생성"""
        await websocket.accept()
        session_id = self.session_manager.create_session(user_id, task_type="qa")
        self.active_connections[session_id] = websocket
        
        logger.info(f"WebSocket 연결: user_id={user_id}, session_id={session_id}")
        return session_id
    
    async def disconnect(self, session_id: str):
        """WebSocket 연결 해제"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        logger.info(f"WebSocket 연결 해제: session_id={session_id}")
    
    async def send_message(self, session_id: str, message: dict):
        """클라이언트에게 메시지 전송"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logger.error(f"메시지 전송 실패: {session_id}, {str(e)}")
                await self.disconnect(session_id)
    
    async def send_status(self, session_id: str, status: str, message: str, progress: int = None):
        """상태 업데이트 전송"""
        await self.send_message(session_id, {
            "type": "status_update",
            "session_id": session_id,
            "data": {
                "status": status,
                "message": message,
                "progress": progress
            },
            "timestamp": self.get_timestamp()
        })
    
    async def send_error(self, session_id: str, error_message: str):
        """에러 메시지 전송"""
        await self.send_message(session_id, {
            "type": "error",
            "session_id": session_id,
            "data": {
                "message": error_message,
                "options": ["다시 시도", "다른 작업 선택", "취소"]
            },
            "timestamp": self.get_timestamp()
        })
    
    # ==================== 메시지 처리 ====================
    
    async def handle_user_message(self, session_id: str, message: str):
        """사용자 메시지 처리 - 어댑터 패턴 활용"""
        try:
            session_data = self.session_manager.get_session(session_id)
            if not session_data:
                await self.send_error(session_id, "세션을 찾을 수 없습니다.")
                return
            
            user_id = session_data["user_id"]
            waiting_for = session_data.get("waiting_for")
            
            # 현재 대기 중인 입력이 있는지 확인
            if waiting_for:
                await self.handle_pending_input(session_id, message, waiting_for)
            else:
                # 새로운 메시지 - 목적 판단 후 해당 어댑터 실행
                await self.handle_new_message(session_id, message, user_id)
                
        except Exception as e:
            logger.error(f"사용자 메시지 처리 오류: {str(e)}")
            await self.send_error(session_id, "메시지 처리 중 오류가 발생했습니다.")
    
    async def handle_new_message(self, session_id: str, message: str, user_id: str):
        """새로운 메시지 처리 - 목적 판단 후 어댑터 실행"""
        try:
            # LangGraph 상태 초기화
            state = get_initial_state(
                user_id=user_id,
                document_id=0,
                pdf_path="",
                purpose="",
                query=message
            )
            
            # 목적 판단 (기존 common.py 로직 활용)
            purpose = await self.judge_purpose(state, message)
            
            # 세션에 상태 저장
            self.session_manager.update_session(session_id, {
                "agent_state": state,
                "task_type": purpose
            })
            
            # 목적에 따라 해당 어댑터 실행
            if purpose == "qa":
                await self.adapter.adapt_qa_flow(session_id, state, message)
            elif purpose == "summary":
                await self.adapter.adapt_summary_flow(session_id, state)
            elif purpose == "generate_exam":
                await self.adapter.adapt_exam_flow(session_id, state)
            elif purpose == "schedule":
                await self.adapter.adapt_schedule_flow(session_id, state)
            else:
                # 기본값은 QA로 처리
                await self.adapter.adapt_qa_flow(session_id, state, message)
                
        except Exception as e:
            logger.error(f"새 메시지 처리 오류: {str(e)}")
            await self.send_error(session_id, "요청을 처리할 수 없습니다.")
    
    async def handle_pending_input(self, session_id: str, message: str, waiting_for: str):
        """대기 중인 입력 처리"""
        try:
            session_data = self.session_manager.get_session(session_id)
            task_type = session_data.get("task_type")
            state = session_data.get("agent_state", {})
            
            if waiting_for == "importance_input":
                # 스케줄러 중요도 입력 파싱
                importance = self.parse_importance_input(message, state.get("subjects", []))
                state["importance"] = importance
                state["scheduler_step"] = "importance_set"
                
                self.session_manager.update_session(session_id, {
                    "agent_state": state,
                    "waiting_for": None
                })
                
                await self.adapter.adapt_schedule_flow(session_id, state)
                
            elif waiting_for in ["deadlines_input", "deadline_input"]:
                # 스케줄러 마감일 입력 파싱 (두 가지 키 모두 처리)
                deadlines = self.parse_deadline_input(message, state.get("subjects", []))
                state["deadlines"] = deadlines
                state["scheduler_step"] = "deadlines_set"
                
                self.session_manager.update_session(session_id, {
                    "agent_state": state,
                    "waiting_for": None
                })
                
                await self.adapter.adapt_schedule_flow(session_id, state)
            
            else:
                # 일반 QA로 처리
                await self.adapter.adapt_qa_flow(session_id, state, message)
                
        except Exception as e:
            logger.error(f"대기 입력 처리 오류: {str(e)}")
            await self.send_error(session_id, "입력 처리 중 오류가 발생했습니다.")
    
    async def handle_file_selection(self, session_id: str, selected_files: list, skip: bool = False):
        """파일 선택 처리"""
        try:
            session_data = self.session_manager.get_session(session_id)
            task_type = session_data.get("task_type")
            request_type = session_data.get("current_request_type")
            state = session_data.get("agent_state", {})
            
            if task_type == "summary":
                # 요약: 선택된 파일로 즉시 실행
                if selected_files:
                    state["pdf_path"] = selected_files[0]
                    self.session_manager.update_session(session_id, {
                        "agent_state": state,
                        "waiting_for": None
                    })
                    await self.adapter.adapt_summary_flow(session_id, state)
                
            elif task_type == "generate_exam":
                if request_type == "previous_exam":
                    # 기출문제 선택됨 또는 스킵
                    if not skip and selected_files:
                        state["previous_exam_path"] = selected_files
                    state["exam_step"] = "previous_exam_selected"
                    
                elif request_type == "study_material":
                    # 학습자료 선택됨
                    if selected_files:
                        state["exam_docs_path"] = selected_files[0]
                        state["exam_step"] = "study_material_selected"
                
                self.session_manager.update_session(session_id, {
                    "agent_state": state,
                    "waiting_for": None
                })
                await self.adapter.adapt_exam_flow(session_id, state)
                
            elif task_type == "schedule":
                # 스케줄러: 선택된 파일들로 과목 추출
                if selected_files:
                    subjects = self.extract_subjects_from_files(selected_files)
                    state.update({
                        "selected_files": selected_files,
                        "subjects": subjects,
                        "scheduler_step": "materials_selected"
                    })
                    
                    self.session_manager.update_session(session_id, {
                        "agent_state": state,
                        "waiting_for": None
                    })
                    await self.adapter.adapt_schedule_flow(session_id, state)
                
        except Exception as e:
            logger.error(f"파일 선택 처리 오류: {str(e)}")
            await self.send_error(session_id, "파일 처리 중 오류가 발생했습니다.")
    
    # ==================== 헬퍼 메서드들 ====================
    
    async def judge_purpose(self, state: dict, message: str) -> str:
        """목적 판단 (기존 common.py 로직 활용)"""
        from app.services.pdf_agent.nodes.common import judge_the_purpose_of_the_input
        
        # 메시지를 상태에 추가
        from langchain_core.messages import HumanMessage
        messages = state.get("messages", [])
        messages.append(HumanMessage(content=message))
        state["messages"] = messages
        
        try:
            result = judge_the_purpose_of_the_input(state)
            return result.get("purpose", "qa")
        except:
            return "qa"  # 실패 시 기본값
    
    def parse_importance_input(self, message: str, subjects: list) -> dict:
        """중요도 입력 파싱: '과목1: 5, 과목2: 3' 형태"""
        importance = {}
        try:
            parts = message.split(',')
            for part in parts:
                if ':' in part:
                    subject, value = part.split(':', 1)
                    subject = subject.strip()
                    try:
                        importance[subject] = int(value.strip())
                    except ValueError:
                        continue
        except:
            # 파싱 실패 시 기본값
            for i, subject in enumerate(subjects):
                importance[subject] = 3  # 기본 중요도
        
        return importance
    
    def parse_deadline_input(self, message: str, subjects: list) -> dict:
        """마감일 입력 파싱: '과목1: 2025-06-01, 과목2: 2025-06-03' 형태"""
        deadlines = {}
        try:
            parts = message.split(',')
            for part in parts:
                if ':' in part:
                    subject, date_str = part.split(':', 1)
                    subject = subject.strip()
                    date_str = date_str.strip()
                    
                    # 간단한 날짜 형식 검증
                    if len(date_str) == 10 and date_str.count('-') == 2:
                        deadlines[subject] = date_str
        except:
            # 파싱 실패 시 기본값
            from datetime import datetime, timedelta
            base_date = datetime.now()
            for i, subject in enumerate(subjects):
                future_date = base_date + timedelta(days=7 + i*3)
                deadlines[subject] = future_date.strftime('%Y-%m-%d')
        
        return deadlines
    
    def extract_subjects_from_files(self, file_paths: list) -> list:
        """파일 경로에서 과목명 추출"""
        subjects = []
        for path in file_paths:
            # 파일명에서 확장자 제거하고 과목명으로 사용
            import os
            filename = os.path.basename(path)
            subject = filename.replace('.pdf', '').replace('_', ' ').replace('-', ' ')
            subjects.append(subject)
        return subjects
    
    def get_timestamp(self) -> str:
        """현재 타임스탬프 반환"""
        return datetime.now().isoformat()

# ==================== WebSocket 엔드포인트 ====================

# 개선된 WebSocket 매니저 인스턴스
improved_manager = ImprovedWebSocketManager()

@router.websocket("/improved-chat/{user_id}")
async def improved_websocket_endpoint(
    websocket: WebSocket, 
    user_id: str
):
    """
    개선된 WebSocket 채팅 엔드포인트
    어댑터 패턴을 통해 기존 Graph/Node와 연결
    """
    session_id = await improved_manager.connect(websocket, user_id)
    
    try:
        while True:
            # 메시지 수신
            data = await websocket.receive_text()
            message_data = json.loads(data)
            message_type = message_data.get("type")
            
            if not message_type:
                await improved_manager.send_error(session_id, "메시지 타입이 지정되지 않았습니다.")
                continue
            
            if message_type == "user_message":
                # 사용자 메시지 처리
                await improved_manager.handle_user_message(
                    session_id,
                    message_data["data"]["message"]
                )
                
            elif message_type == "file_selection":
                # 파일 선택 처리
                await improved_manager.handle_file_selection(
                    session_id,
                    message_data["data"]["selected_files"],
                    message_data["data"].get("skip", False)
                )
                
            elif message_type == "error_choice":
                # 에러 처리 선택
                choice = message_data["data"]["choice"]
                if choice == "다시 시도":
                    # 이전 작업 재시도
                    session_data = improved_manager.session_manager.get_session(session_id)
                    task_type = session_data.get("task_type")
                    state = session_data.get("agent_state", {})
                    
                    if task_type == "summary":
                        await improved_manager.adapter.adapt_summary_flow(session_id, state)
                    elif task_type == "generate_exam":
                        await improved_manager.adapter.adapt_exam_flow(session_id, state)
                    elif task_type == "schedule":
                        await improved_manager.adapter.adapt_schedule_flow(session_id, state)
                        
                elif choice == "다른 작업 선택":
                    # 세션 초기화
                    improved_manager.session_manager.update_session(session_id, {
                        "task_type": "qa",
                        "waiting_for": None,
                        "agent_state": {}
                    })
                    await improved_manager.send_message(session_id, {
                        "type": "ai_response",
                        "session_id": session_id,
                        "data": {
                            "message": "새로운 작업을 요청해 주세요.",
                            "task_type": "qa",
                            "is_final": False
                        },
                        "timestamp": improved_manager.get_timestamp()
                    })
                    
                elif choice == "취소":
                    # 현재 작업 취소
                    improved_manager.session_manager.update_session(session_id, {
                        "waiting_for": None
                    })
                    await improved_manager.send_message(session_id, {
                        "type": "ai_response",
                        "session_id": session_id,
                        "data": {
                            "message": "작업이 취소되었습니다.",
                            "task_type": "qa",
                            "is_final": False
                        },
                        "timestamp": improved_manager.get_timestamp()
                    })
                
            elif message_type == "ping":
                # 연결 유지용 핑
                await improved_manager.send_message(session_id, {
                    "type": "pong",
                    "session_id": session_id,
                    "timestamp": improved_manager.get_timestamp()
                })
                
    except WebSocketDisconnect:
        await improved_manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket 오류: {str(e)}")
        await improved_manager.disconnect(session_id)

# ==================== REST API 엔드포인트들 ====================

@router.get("/improved-chat/sessions/{user_id}")
async def get_improved_chat_sessions(
    user_id: str,
    limit: int = 20,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """사용자의 개선된 채팅 세션 목록 조회"""
    try:
        # 권한 확인
        if current_user.id != int(user_id) and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        
        sessions = improved_manager.session_manager.get_user_chat_sessions(user_id, limit)
        return {
            "sessions": sessions,
            "total": len(sessions),
            "manager_type": "improved"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"개선된 채팅 세션 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="세션 목록 조회 중 오류가 발생했습니다.")

@router.post("/improved-chat/sessions/{user_id}/new")
async def create_improved_chat_session(
    user_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """개선된 채팅 세션 생성"""
    try:
        # 권한 확인
        if current_user.id != int(user_id) and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        
        session_id = improved_manager.session_manager.create_session(user_id, task_type="qa")
        
        return {
            "session_id": session_id,
            "message": "새 개선된 채팅 세션이 생성되었습니다.",
            "manager_type": "improved"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"새 개선된 채팅 세션 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="세션 생성 중 오류가 발생했습니다.")