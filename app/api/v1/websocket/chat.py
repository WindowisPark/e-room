# app/api/v1/websocket/chat.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from fastapi.responses import JSONResponse
from langchain_core.messages import HumanMessage, AIMessage
from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from app.services.session_manager import SessionManager
from app.services.pdf_agent.tools import get_initial_state
from app.services.pdf_agent.graphs.main import intergrate_graph
from app.api import deps
from app.models.user import User
from app.api.v1.websocket.handlers import TaskHandlers
from app.services.s3_file_service import S3StorageManager
from app.core.config import settings
import json
import asyncio
import logging
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.session_manager = SessionManager()
        self.agent_graph = intergrate_graph()
        self.task_handlers = TaskHandlers(self)  # 작업 핸들러 추가

    async def connect(self, websocket: WebSocket, user_id: str) -> str:
        """WebSocket 연결 및 세션 생성"""
        await websocket.accept()
        # QA 타입으로 기본 세션 생성
        session_id = self.session_manager.create_session(user_id, task_type="qa")
        self.active_connections[session_id] = websocket

        # 프론트엔드에 세션 ID 즉시 통보 (로컬 임시 ID와 동기화용)
        await websocket.send_text(json.dumps({
            "type": "session_connected",
            "session_id": session_id,
            "timestamp": self.get_timestamp()
        }, ensure_ascii=False))

        logger.info(f"WebSocket 연결: user_id={user_id}, session_id={session_id}")
        return session_id

    async def disconnect(self, session_id: str):
        """WebSocket 연결 해제"""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        
        # 세션은 유지 (나중에 재연결 가능)
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

    async def handle_user_message(self, session_id: str, message: str):
        """사용자 메시지 처리"""
        try:
            session_data = self.session_manager.get_session(session_id)
            if not session_data:
                await self.send_error(session_id, "세션을 찾을 수 없습니다.")
                return

            user_id = session_data["user_id"]
            
            # 사용자 메시지를 히스토리에 추가
            user_message = HumanMessage(content=message)
            self.session_manager.add_message_to_history(session_id, user_message)
            
            # 첫 메시지인지 확인
            if session_data.get("agent_state") is None or len(session_data.get("message_history", [])) <= 1:
                # 첫 메시지 - 목적 판단
                await self.handle_first_message(session_id, message, user_id)
            else:
                # 기존 대화 - 현재 작업 타입에 따라 처리
                task_type = session_data.get("task_type", "qa")
                if task_type == "qa":
                    await self.handle_qa_continue(session_id, message, session_data)
                else:
                    # 다른 작업 타입 처리
                    await self.handle_other_task_continue(session_id, message, session_data)
                    
        except Exception as e:
            logger.error(f"사용자 메시지 처리 오류: {str(e)}")
            await self.send_error(session_id, "메시지 처리 중 오류가 발생했습니다.")

    async def handle_first_message(self, session_id: str, message: str, user_id: str):
        """첫 메시지 처리 및 목적 판단"""
        try:
            # LangGraph 상태 초기화
            state = get_initial_state(
                user_id=user_id,
                document_id=0,
                pdf_path="",
                purpose="",
                query=message
            )
            
            # 목적 판단 실행
            await self.send_status(session_id, "processing", "요청을 분석하고 있습니다...")
            
            result = await self.run_agent_step(state, "judge_the_purpose_of_the_input")
            purpose = result.get("purpose", "qa")
            
            # 세션에 상태 저장
            session_data = {
                "agent_state": result,
                "task_type": purpose
            }
            self.session_manager.update_session(session_id, session_data)
            
            # 목적에 따라 분기
            if purpose == "qa":
                await self.handle_qa(session_id, result)
            elif purpose == "summary":
                await self.handle_summary_start(session_id, result)
            elif purpose == "generate_exam":
                await self.handle_exam_start(session_id, result)
            elif purpose == "schedule":
                await self.handle_scheduler_start(session_id, result)
            else:
                # 기본적으로 QA로 처리
                await self.handle_qa(session_id, result)
                
        except Exception as e:
            logger.error(f"첫 메시지 처리 오류: {str(e)}")
            await self.send_error(session_id, "요청을 처리할 수 없습니다.")

    async def handle_qa(self, session_id: str, state: dict):
        """QA 처리 - 바로 응답"""
        try:
            await self.send_status(session_id, "processing", "답변을 생성하고 있습니다...")

            # QA 에이전트 실행
            result = await self.run_agent_step(state, "start_point_of_qa_system")
            messages = result.get("messages", [])
            response_content = messages[-1].content if messages else "답변을 생성할 수 없습니다."
            
            # AI 응답을 히스토리에 추가
            ai_message = AIMessage(content=response_content)
            self.session_manager.add_message_to_history(session_id, ai_message)
            
            # 응답 전송
            await self.send_message(session_id, {
                "type": "ai_response",
                "session_id": session_id,
                "data": {
                    "message": response_content,
                    "task_type": "qa",
                    "is_final": False  # QA는 대화가 계속될 수 있음
                },
                "timestamp": self.get_timestamp()
            })
            
            # 에이전트 상태 업데이트
            self.session_manager.update_session(session_id, {"agent_state": result})
            
        except Exception as e:
            logger.error(f"QA 처리 오류: {str(e)}")
            await self.send_error(session_id, "답변 생성 중 오류가 발생했습니다.")

    async def handle_qa_continue(self, session_id: str, message: str, session_data: dict):
        """QA 대화 계속하기"""
        try:
            # 기존 대화 히스토리를 포함한 상태로 업데이트
            current_state = session_data["agent_state"]
            
            # 메시지 히스토리를 LangGraph 메시지 형태로 변환
            message_history = session_data.get("message_history", [])
            langchain_messages = []
            
            for msg in message_history:
                if msg["type"] == "HumanMessage":
                    langchain_messages.append(HumanMessage(content=msg["content"]))
                elif msg["type"] == "AIMessage":
                    langchain_messages.append(AIMessage(content=msg["content"]))
            
            # 현재 상태에 메시지 히스토리 포함
            current_state["messages"] = langchain_messages
            current_state["last_user_query"] = message
            
            await self.send_status(session_id, "processing", "답변을 생성하고 있습니다...")
            
            # QA 에이전트 재실행
            result = await self.run_agent_step(current_state, "start_point_of_qa_system")
            messages = result.get("messages", [])
            response_content = messages[-1].content if messages else "답변을 생성할 수 없습니다."
            
            # AI 응답을 히스토리에 추가
            ai_message = AIMessage(content=response_content)
            self.session_manager.add_message_to_history(session_id, ai_message)
            
            # 응답 전송
            await self.send_message(session_id, {
                "type": "ai_response",
                "session_id": session_id,
                "data": {
                    "message": response_content,
                    "task_type": "qa",
                    "is_final": False
                },
                "timestamp": self.get_timestamp()
            })
            
            # 에이전트 상태 업데이트
            self.session_manager.update_session(session_id, {"agent_state": result})
            
        except Exception as e:
            logger.error(f"QA 대화 계속 처리 오류: {str(e)}")
            await self.send_error(session_id, "답변 생성 중 오류가 발생했습니다.")

    async def handle_summary_start(self, session_id: str, state: dict):
        """요약 시작 - 파일 선택 요청"""
        try:
            session_data = self.session_manager.get_session(session_id)
            user_id = session_data["user_id"]
            
            # 사용자 파일 목록 조회
            available_files = await self.get_user_files(user_id)
            
            await self.send_message(session_id, {
                "type": "file_request",
                "session_id": session_id,
                "data": {
                    "message": "어떤 자료를 요약해드릴까요?",
                    "request_type": "summary_target",
                    "multiple": False,
                    "optional": False,
                    "available_files": available_files
                },
                "timestamp": self.get_timestamp()
            })
            
            # 세션 상태 업데이트
            update_data = {
                "waiting_for": "file_selection",
                "current_request_type": "summary_target"
            }
            self.session_manager.update_session(session_id, update_data)
            
        except Exception as e:
            logger.error(f"요약 시작 오류: {str(e)}")
            await self.send_error(session_id, "요약을 시작할 수 없습니다.")

    async def handle_exam_start(self, session_id: str, state: dict):
        """시험 문제 생성 시작 - 기출문제 선택부터"""
        try:
            session_data = self.session_manager.get_session(session_id)
            user_id = session_data["user_id"]
            
            # 사용자 파일 목록 조회
            available_files = await self.get_user_files(user_id)
            
            await self.send_message(session_id, {
                "type": "file_request",
                "session_id": session_id,
                "data": {
                    "message": "기출문제가 있나요? (선택사항)",
                    "request_type": "previous_exam",
                    "multiple": True,
                    "optional": True,
                    "available_files": available_files
                },
                "timestamp": self.get_timestamp()
            })
            
            # 세션 상태 업데이트
            update_data = {
                "waiting_for": "file_selection",
                "current_request_type": "previous_exam",
                "exam_step": "previous_exam_selection"
            }
            self.session_manager.update_session(session_id, update_data)
            
        except Exception as e:
            logger.error(f"시험 문제 생성 시작 오류: {str(e)}")
            await self.send_error(session_id, "시험 문제 생성을 시작할 수 없습니다.")

    async def handle_scheduler_start(self, session_id: str, state: dict):
        """스케줄러 시작 - 학습 자료 선택부터"""
        try:
            session_data = self.session_manager.get_session(session_id)
            user_id = session_data["user_id"]
            
            # 사용자 파일 목록 조회
            available_files = await self.get_user_files(user_id)
            
            await self.send_message(session_id, {
                "type": "file_request",
                "session_id": session_id,
                "data": {
                    "message": "공부할 자료들을 선택해주세요 (여러 개 선택 가능)",
                    "request_type": "scheduler_materials",
                    "multiple": True,
                    "optional": False,
                    "available_files": available_files
                },
                "timestamp": self.get_timestamp()
            })
            
            # 세션 상태 업데이트
            update_data = {
                "waiting_for": "file_selection",
                "current_request_type": "scheduler_materials",
                "scheduler_step": "material_selection",
                "scheduler_data": {
                    "selected_materials": [],
                    "subjects": [],
                    "importance": {},
                    "deadlines": {}
                }
            }
            self.session_manager.update_session(session_id, update_data)
            
        except Exception as e:
            logger.error(f"스케줄러 시작 오류: {str(e)}")
            await self.send_error(session_id, "스케줄 생성을 시작할 수 없습니다.")

    async def handle_other_task_continue(self, session_id: str, message: str, session_data: dict):
        """다른 작업 타입 계속 처리"""
        task_type = session_data.get("task_type")
        scheduler_step = session_data.get("scheduler_step", "")
        waiting_for = session_data.get("waiting_for")
        
        # 스케줄러의 텍스트 입력 처리
        if task_type == "schedule" and waiting_for in ["importance_input", "deadline_input"]:
            if waiting_for == "importance_input":
                await self.process_importance_input(session_id, message)
            elif waiting_for == "deadline_input":
                await self.process_deadline_input(session_id, message)
        else:
            # 다른 작업이 완료된 경우 QA 모드로 전환
            await self.convert_to_qa_mode(session_id, message, session_data)
    
    async def convert_to_qa_mode(self, session_id: str, message: str, session_data: dict):
        """다른 작업 완료 후 QA 모드로 전환"""
        try:
            # 사용자 메시지를 히스토리에 추가
            user_message = HumanMessage(content=message)
            self.session_manager.add_message_to_history(session_id, user_message)
            
            # QA 모드로 변경
            update_data = {
                "task_type": "qa",
                "waiting_for": None,
                "current_request_type": None
            }
            self.session_manager.update_session(session_id, update_data)
            
            # QA 처리
            await self.handle_qa_continue(session_id, message, session_data)
            
        except Exception as e:
            logger.error(f"QA 모드 전환 오류: {str(e)}")
            await self.send_error(session_id, "메시지 처리 중 오류가 발생했습니다.")

    # 기존 메서드들을 TaskHandlers로 위임
    async def handle_file_selection(self, session_id: str, selected_files: list, skip: bool = False):
        """파일 선택 처리를 TaskHandlers로 위임"""
        return await self.task_handlers.handle_file_selection(session_id, selected_files, skip)
    
    async def handle_importance_input(self, session_id: str, importance_data: dict):
        """중요도 입력 처리를 TaskHandlers로 위임"""
        return await self.task_handlers.handle_importance_input(session_id, importance_data)
    
    async def handle_deadline_input(self, session_id: str, deadline_data: dict):
        """마감일 입력 처리를 TaskHandlers로 위임"""
        return await self.task_handlers.handle_deadline_input(session_id, deadline_data)
    
    async def process_importance_input(self, session_id: str, message: str):
        """중요도 입력 텍스트 파싱을 TaskHandlers로 위임"""
        session_data = self.session_manager.get_session(session_id)
        scheduler_data = session_data.get("scheduler_data", {})
        return await self.task_handlers.process_importance_input(session_id, message, scheduler_data)
    
    async def process_deadline_input(self, session_id: str, message: str):
        """마감일 입력 텍스트 파싱을 TaskHandlers로 위임"""
        session_data = self.session_manager.get_session(session_id)
        scheduler_data = session_data.get("scheduler_data", {})
        return await self.task_handlers.process_deadline_input(session_id, message, scheduler_data)

    async def run_agent_step(self, state: dict, step_name: str) -> dict:
        """LangGraph 에이전트 스텝 실행"""
        return await asyncio.get_event_loop().run_in_executor(
            None, 
            lambda: self.agent_graph.invoke(state)
        )

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
                "message": error_message
            },
            "timestamp": self.get_timestamp()
        })
    async def get_user_files(self, user_id: str) -> list:
        """사용자의 S3 PDF 파일 목록을 WebSocket용 포맷으로 반환"""
        try:
            s3 = S3StorageManager()
            folders = s3.list_folders(user_id)
            results = []

            for folder in folders:
                files = s3.list_files(user_id, folder.name)
                for file_name in files:
                    if not file_name.lower().endswith(".pdf"):
                        continue  # PDF만 필터링

                    file_path = f"users/{user_id}/{folder.name}/{file_name}"
                    results.append({
                        "name": file_name,
                        "folder": folder.name,
                        "path": file_path,
                        "type": "pdf"
                    })

            return results

        except Exception as e:
            logger.error(f"S3 파일 목록 조회 실패: {str(e)}")
            return []

    def get_timestamp(self) -> str:
        """현재 타임스탬프 반환"""
        return datetime.now().isoformat()

# WebSocket 매니저 인스턴스
manager = WebSocketManager()

@router.websocket("/chat/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=4001)
        return
    try:
        import jwt
        payload = jwt.decode(token, settings.ACCESS_SECRET_KEY, algorithms=["HS256"])
        token_user_id = str(payload.get("sub"))
        if token_user_id != user_id:
            await websocket.close(code=4003)
            return
    except Exception:
        await websocket.close(code=4001)
        return

    session_id = await manager.connect(websocket, user_id)
    
    try:
        while True:
            # 메시지 수신
            data = await websocket.receive_text()
            message_data = json.loads(data)           
            message_type = message_data.get("type")

            if not message_type:
                logger.warning("⚠️ message_type 누락됨")
                await manager.send_error(session_id, "메시지 타입이 지정되지 않았습니다.")
                continue
            
            if message_type == "user_message":
                await manager.handle_user_message(
                    session_id, 
                    message_data["data"]["message"]
                )
            elif message_type == "file_selection":
                await manager.handle_file_selection(
                    session_id,
                    message_data["data"]["selected_files"],
                    message_data["data"].get("skip", False)
                )
            elif message_type == "importance_input":
                # 스케줄러 중요도 입력
                await manager.handle_importance_input(
                    session_id,
                    message_data["data"]
                )
            elif message_type == "deadline_input":
                # 스케줄러 마감일 입력
                await manager.handle_deadline_input(
                    session_id,
                    message_data["data"]
                )
            elif message_type == "ping":
                # 연결 유지용 핑
                await manager.send_message(session_id, {
                    "type": "pong",
                    "session_id": session_id,
                    "timestamp": manager.get_timestamp()
                })
                
    except WebSocketDisconnect:
        await manager.disconnect(session_id)
    except Exception as e:
        logger.error(f"WebSocket 오류: {str(e)}")
        await manager.disconnect(session_id)

# REST API 엔드포인트들

@router.get("/chat/sessions/{user_id}")
async def get_user_chat_sessions(
    user_id: str,
    limit: int = 20,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    사용자의 채팅 세션 목록 조회
    
    Args:
        user_id: 사용자 ID
        limit: 최대 조회 개수
    """
    try:
        # 권한 확인
        if current_user.id != int(user_id) and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        
        sessions = manager.session_manager.get_user_chat_sessions(user_id, limit)
        return {
            "sessions": sessions,
            "total": len(sessions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"채팅 세션 목록 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="세션 목록 조회 중 오류가 발생했습니다.")

@router.get("/chat/sessions/{session_id}/history")
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    특정 채팅의 메시지 히스토리 조회
    
    Args:
        session_id: 세션 ID
    """
    try:
        # 세션 소유자 확인
        session_data = manager.session_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        if current_user.id != int(session_data["user_id"]) and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        
        history = manager.session_manager.get_chat_history(session_id)
        
        return {
            "session_id": session_id,
            "title": session_data.get("chat_title", "새 채팅"),
            "created_at": session_data.get("created_at"),
            "message_history": history,
            "message_count": len(history)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"채팅 히스토리 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="히스토리 조회 중 오류가 발생했습니다.")

@router.post("/chat/sessions/{user_id}/new")
async def create_new_chat_session(
    user_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    새 채팅 세션 생성
    
    Args:
        user_id: 사용자 ID
    """
    try:
        # 권한 확인
        if current_user.id != int(user_id) and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        
        session_id = manager.session_manager.create_session(user_id, task_type="qa")
        
        return {
            "session_id": session_id,
            "message": "새 채팅 세션이 생성되었습니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"새 채팅 세션 생성 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="세션 생성 중 오류가 발생했습니다.")

@router.delete("/chat/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    채팅 세션 삭제
    
    Args:
        session_id: 세션 ID
    """
    try:
        # 세션 소유자 확인
        session_data = manager.session_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        if current_user.id != int(session_data["user_id"]) and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        
        success = manager.session_manager.cleanup_session(session_id)
        
        if success:
            return {"message": "채팅 세션이 삭제되었습니다."}
        else:
            raise HTTPException(status_code=500, detail="세션 삭제에 실패했습니다.")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"채팅 세션 삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="세션 삭제 중 오류가 발생했습니다.")

@router.patch("/chat/sessions/{session_id}/title")
async def update_chat_title(
    session_id: str,
    title_data: dict,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    채팅 제목 수정
    
    Args:
        session_id: 세션 ID
        title_data: {"title": "새 제목"}
    """
    try:
        # 세션 소유자 확인
        session_data = manager.session_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        if current_user.id != int(session_data["user_id"]) and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        
        new_title = title_data.get("title", "").strip()
        if not new_title:
            raise HTTPException(status_code=400, detail="제목을 입력해주세요.")
        
        # 제목 길이 제한
        if len(new_title) > 100:
            new_title = new_title[:100]
        
        success = manager.session_manager.update_session(session_id, {"chat_title": new_title})
        
        if success:
            return {
                "session_id": session_id,
                "title": new_title,
                "message": "제목이 변경되었습니다."
            }
        else:
            raise HTTPException(status_code=500, detail="제목 변경에 실패했습니다.")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"채팅 제목 변경 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="제목 변경 중 오류가 발생했습니다.")

@router.get("/chat/sessions/{user_id}/stats")
async def get_user_chat_stats(
    user_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    사용자 채팅 통계 조회
    
    Args:
        user_id: 사용자 ID
    """
    try:
        # 권한 확인
        if current_user.id != int(user_id) and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        
        stats = manager.session_manager.get_session_stats(user_id)
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"채팅 통계 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="통계 조회 중 오류가 발생했습니다.")

@router.post("/chat/sessions/{session_id}/reconnect")
async def reconnect_to_session(
    session_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """
    기존 세션에 재연결
    
    Args:
        session_id: 세션 ID
    """
    try:
        # 세션 존재 확인
        session_data = manager.session_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        # 세션 소유자 확인
        if current_user.id != int(session_data["user_id"]) and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        
        # TTL 연장
        manager.session_manager.extend_session_ttl(session_id)
        
        return {
            "session_id": session_id,
            "title": session_data.get("chat_title", "새 채팅"),
            "task_type": session_data.get("task_type", "qa"),
            "message": "세션에 재연결되었습니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"세션 재연결 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="재연결 중 오류가 발생했습니다.")