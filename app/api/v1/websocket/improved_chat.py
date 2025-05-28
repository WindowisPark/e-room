# app/api/v1/websocket/improved_chat.py
"""
기존 chat.py를 개선한 버전
WebSocket 어댑터 패턴을 활용하여 Graph/Node와 연결
JSON 파싱 오류 및 연결 해제 오류 완전 수정 버전
"""

import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from starlette.websockets import WebSocketState

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
        """클라이언트에게 메시지 전송 + DB 저장"""
        if session_id in self.active_connections:
            websocket = self.active_connections[session_id]
            try:
                await websocket.send_text(json.dumps(message, ensure_ascii=False))
                
                # 🆕 AI 응답을 DB에 저장
                if message.get("type") == "ai_response":
                    content = message.get("data", {}).get("message", "")
                    extra_data = {  # ✅ metadata → extra_data
                        "task_type": message.get("data", {}).get("task_type"),
                        "is_final": message.get("data", {}).get("is_final")
                    }
                    self.session_manager.add_message_to_history(
                        session_id, 
                        content,  # ← 그냥 문자열로
                        extra_data
                    )
                    
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
        """사용자 메시지 처리 - 어댑터 패턴 활용 + DB 저장"""
        try:
            # 🔧 수정: 문자열을 HumanMessage 객체로 변환해서 저장
            from langchain_core.messages import HumanMessage
            
            # 사용자 메시지를 DB에 저장 (HumanMessage 객체로)
            human_message = HumanMessage(content=message)
            self.session_manager.add_message_to_history(session_id, human_message)
            
            session_data = self.session_manager.get_session(session_id)
            if not session_data:
                await self.send_error(session_id, "세션을 찾을 수 없습니다.")
                return
            
            user_id = session_data["user_id"]
            waiting_for = session_data.get("waiting_for")
            
            logger.info(f"사용자 메시지 처리: session_id={session_id}, waiting_for={waiting_for}")
            logger.debug(f"메시지 내용: {message}")
            
            # 현재 대기 중인 입력이 있는지 확인
            if waiting_for:
                await self.handle_pending_input(session_id, message, waiting_for)
            else:
                # 새로운 메시지 - 목적 판단 후 해당 어댑터 실행
                await self.handle_new_message(session_id, message, user_id)
                
        except Exception as e:
            logger.error(f"사용자 메시지 처리 오류: {str(e)}", exc_info=True)
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
            logger.info(f"목적 판단 결과: {purpose}")
            
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
            logger.error(f"새 메시지 처리 오류: {str(e)}", exc_info=True)
            await self.send_error(session_id, "요청을 처리할 수 없습니다.")
    
    async def handle_pending_input(self, session_id: str, message: str, waiting_for: str):
        """대기 중인 입력 처리"""
        try:
            session_data = self.session_manager.get_session(session_id)
            task_type = session_data.get("task_type")
            state = session_data.get("agent_state", {})
            
            logger.info(f"대기 입력 처리: waiting_for={waiting_for}, task_type={task_type}")
            logger.info(f"입력 메시지: {message}")

            if waiting_for == "importance_input":
                # 스케줄러 중요도 입력 파싱
                importance = self.parse_importance_input(message, state.get("subjects", []))
                subjects = state.get("subjects", []) 
                logger.info(f"중요도 파싱 결과: {importance}")
                logger.info(f"현재 subjects: {subjects}")  # ← 추가
                
                state["importance"] = importance
                state["scheduler_step"] = "importance_set"
                
                self.session_manager.update_session(session_id, {
                    "agent_state": state,
                    "waiting_for": None
                })
                logger.info("세션 업데이트 완료")  # ← 이렇게 변경
                
                
                await self.adapter.adapt_schedule_flow(session_id, state)
                
            elif waiting_for in ["deadlines_input", "deadline_input"]:
                # 스케줄러 마감일 입력 파싱 (두 가지 키 모두 처리)
                deadlines = self.parse_deadline_input(message, state.get("subjects", []))
                logger.info(f"마감일 파싱 결과: {deadlines}")
                
                state["deadlines"] = deadlines
                state["scheduler_step"] = "deadlines_set"
                
                self.session_manager.update_session(session_id, {
                    "agent_state": state,
                    "waiting_for": None
                })
                
                await self.adapter.adapt_schedule_flow(session_id, state)
            
            else:
                # 일반 QA로 처리
                logger.info(f"알 수 없는 waiting_for: {waiting_for}, QA로 처리")
                await self.adapter.adapt_qa_flow(session_id, state, message)
                
        except Exception as e:
            logger.error(f"대기 입력 처리 오류: {str(e)}", exc_info=True)
            await self.send_error(session_id, "입력 처리 중 오류가 발생했습니다.")
    
    async def handle_file_selection(self, session_id: str, selected_files: list, skip: bool = False):
        """파일 선택 처리"""
        try:
            session_data = self.session_manager.get_session(session_id)
            if not session_data:
                await self.send_error(session_id, "세션을 찾을 수 없습니다.")
                return
                
            task_type = session_data.get("task_type")
            request_type = session_data.get("current_request_type")
            state = session_data.get("agent_state", {})
            
            logger.info(f"파일 선택 처리: task_type={task_type}, request_type={request_type}, skip={skip}")
            logger.debug(f"선택된 파일: {selected_files}")
            
            if task_type == "summary":
                # 요약: 선택된 파일로 즉시 실행
                if selected_files:
                    state["pdf_path"] = selected_files[0]
                    self.session_manager.update_session(session_id, {
                        "agent_state": state,
                        "waiting_for": None,
                        "current_request_type": None
                    })
                    await self.adapter.adapt_summary_flow(session_id, state)
                else:
                    await self.send_error(session_id, "요약할 파일을 선택해주세요.")
                
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
                    else:
                        await self.send_error(session_id, "학습자료를 선택해주세요.")
                        return
                
                self.session_manager.update_session(session_id, {
                    "agent_state": state,
                    "waiting_for": None,
                    "current_request_type": None
                })
                await self.adapter.adapt_exam_flow(session_id, state)
                
            elif task_type == "schedule":
                # 스케줄러: 선택된 파일들로 과목 추출
                if selected_files:
                    subjects = self.extract_subjects_from_files(selected_files)
                    logger.info(f"추출된 과목: {subjects}")
                    
                    state.update({
                        "selected_files": selected_files,
                        "subjects": subjects,
                        "scheduler_step": "materials_selected"
                    })
                    
                    self.session_manager.update_session(session_id, {
                        "agent_state": state,
                        "waiting_for": None,
                        "current_request_type": None
                    })
                    await self.adapter.adapt_schedule_flow(session_id, state)
                else:
                    await self.send_error(session_id, "학습자료를 선택해주세요.")
                
        except Exception as e:
            logger.error(f"파일 선택 처리 오류: {str(e)}", exc_info=True)
            await self.send_error(session_id, "파일 처리 중 오류가 발생했습니다.")
    
    # ==================== 헬퍼 메서드들 ====================
    
    async def judge_purpose(self, state: dict, message: str) -> str:
        """목적 판단 (기존 common.py 로직 활용)"""
        try:
            from app.services.pdf_agent.nodes.common import judge_the_purpose_of_the_input
            
            # 메시지를 상태에 추가
            from langchain_core.messages import HumanMessage
            messages = state.get("messages", [])
            messages.append(HumanMessage(content=message))
            state["messages"] = messages
            
            result = judge_the_purpose_of_the_input(state)
            purpose = result.get("purpose", "qa")
            logger.info(f"목적 판단: '{message}' -> {purpose}")
            return purpose
            
        except Exception as e:
            logger.error(f"목적 판단 실패: {str(e)}")
            return "qa"  # 실패 시 기본값
    
    def parse_importance_input(self, message: str, subjects: list) -> dict:
        """중요도 입력 파싱: '과목1: 5, 과목2: 3' 형태"""
        importance = {}
        try:
            # 쉼표로 분리
            parts = message.split(',')
            for part in parts:
                if ':' in part:
                    subject, value = part.split(':', 1)
                    subject = subject.strip()
                    try:
                        value_int = int(value.strip())
                        # 1-5 범위 확인
                        if 1 <= value_int <= 5:
                            importance[subject] = value_int
                        else:
                            logger.warning(f"중요도 범위 벗어남: {subject}={value_int}")
                    except ValueError:
                        logger.warning(f"중요도 숫자 변환 실패: {subject}={value}")
                        continue
                        
            # 파싱 결과가 없으면 기본값 설정
            if not importance and subjects:
                logger.info("중요도 파싱 실패, 기본값 설정")
                for subject in subjects:
                    importance[subject] = 3  # 기본 중요도
                    
        except Exception as e:
            logger.error(f"중요도 파싱 오류: {str(e)}")
            # 파싱 실패 시 기본값
            for subject in subjects:
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
                    
                    # 날짜 형식 검증 (YYYY-MM-DD)
                    if len(date_str) == 10 and date_str.count('-') == 2:
                        try:
                            # 실제 날짜 파싱 검증
                            from datetime import datetime
                            datetime.strptime(date_str, '%Y-%m-%d')
                            deadlines[subject] = date_str
                        except ValueError:
                            logger.warning(f"잘못된 날짜 형식: {subject}={date_str}")
                            
            # 파싱 결과가 없으면 기본값 설정
            if not deadlines and subjects:
                logger.info("마감일 파싱 실패, 기본값 설정")
                from datetime import datetime, timedelta
                base_date = datetime.now()
                for i, subject in enumerate(subjects):
                    future_date = base_date + timedelta(days=7 + i*3)
                    deadlines[subject] = future_date.strftime('%Y-%m-%d')
                    
        except Exception as e:
            logger.error(f"마감일 파싱 오류: {str(e)}")
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
        try:
            for path in file_paths:
                # 파일명에서 확장자 제거하고 과목명으로 사용
                import os
                filename = os.path.basename(path)
                # 확장자 제거
                subject = os.path.splitext(filename)[0]
                # 특수 문자를 공백으로 치환
                subject = subject.replace('_', ' ').replace('-', ' ').strip()
                if subject:  # 빈 문자열이 아닌 경우만 추가
                    subjects.append(subject)
                    
            # 중복 제거하면서 순서 유지
            unique_subjects = []
            for subject in subjects:
                if subject not in unique_subjects:
                    unique_subjects.append(subject)
                    
            return unique_subjects
            
        except Exception as e:
            logger.error(f"과목명 추출 오류: {str(e)}")
            return ["기본과목"]  # 기본값
    
    def get_timestamp(self) -> str:
        """현재 타임스탬프 반환"""
        return datetime.now().isoformat()


def repair_json(data: str) -> str:
    """손상된 JSON 데이터를 자동으로 복구"""
    data = data.strip()
    
    # 1. 맨 앞 중괄호 누락 확인 및 복구
    if not data.startswith('{') and data.startswith('"'):
        data = '{' + data
        logger.info("JSON 시작 중괄호 추가")
    
    # 2. 맨 뒤 중괄호 누락 확인 및 복구
    if not data.endswith('}') and data.count('{') > data.count('}'):
        data = data + '}'
        logger.info("JSON 끝 중괄호 추가")
    
    # 3. 개행문자 및 캐리지 리턴 제거
    data = data.replace('\r\n', '').replace('\r', '').replace('\n', '')
    
    # 4. 연속된 공백 제거 (JSON 내부는 유지)
    import re
    # JSON 문자열 내부가 아닌 구조적 공백만 정리
    data = re.sub(r':\s+', ': ', data)  # 콜론 뒤 공백 정리
    data = re.sub(r',\s+', ', ', data)  # 쉼표 뒤 공백 정리
    data = re.sub(r'{\s+', '{', data)   # 중괄호 뒤 공백 제거
    data = re.sub(r'\s+}', '}', data)   # 중괄호 앞 공백 제거
    
    return data


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
    연결 해제 오류 완전 해결 버전
    """
    session_id = None
    
    try:
        session_id = await improved_manager.connect(websocket, user_id)
        logger.info(f"WebSocket 연결 성공: session_id={session_id}")
        
        while True:
            try:
                # 📍 핵심 수정: WebSocket 상태를 먼저 확인
                if websocket.application_state == WebSocketState.DISCONNECTED:
                    logger.info("WebSocket이 이미 끊어짐 - 루프 종료")
                    break
                
                # 📍 receive_text() 대신 receive() 사용하여 메시지 타입 확인
                message = await websocket.receive()
                
                # 📍 연결 해제 메시지 체크
                if message.get("type") == "websocket.disconnect":
                    logger.info("연결 해제 메시지 수신")
                    break
                
                # 📍 텍스트 메시지가 아닌 경우 스킵
                if message.get("type") != "websocket.receive":
                    logger.warning(f"예상치 못한 메시지 타입: {message.get('type')}")
                    continue
                
                # 📍 텍스트 데이터 추출
                data = message.get("text", "")
                if not data:
                    logger.warning("빈 텍스트 데이터 수신")
                    continue
                
                logger.debug(f"수신된 원본 데이터: {data}")
                
                # 데이터 정리
                data = data.strip()
                
                # JSON 복구 및 파싱
                try:
                    message_data = json.loads(data)
                except json.JSONDecodeError as json_error:
                    logger.warning(f"첫 번째 JSON 파싱 실패: {json_error}")
                    
                    # JSON 복구 시도
                    try:
                        repaired_data = repair_json(data)
                        logger.info(f"JSON 복구 시도: {repr(repaired_data)}")
                        message_data = json.loads(repaired_data)
                        logger.info("JSON 복구 성공!")
                    except json.JSONDecodeError as repair_error:
                        logger.error(f"JSON 복구도 실패: {repair_error}")
                        logger.error(f"복구 시도한 데이터: {repr(repaired_data)}")
                        
                        await improved_manager.send_error(
                            session_id, 
                            f"JSON 형식 오류입니다. 원본: {str(json_error)}"
                        )
                        continue
                
                message_type = message_data.get("type")
                
                if not message_type:
                    logger.warning("메시지 타입 누락")
                    await improved_manager.send_error(session_id, "메시지 타입이 지정되지 않았습니다.")
                    continue
                
                logger.info(f"처리할 메시지 타입: {message_type}")
                
                # 메시지 타입별 처리
                if message_type == "user_message":
                    message_content = message_data.get("data", {}).get("message", "")
                    if not message_content.strip():
                        await improved_manager.send_error(session_id, "메시지 내용을 입력해주세요.")
                        continue
                        
                    await improved_manager.handle_user_message(session_id, message_content)
                    
                elif message_type == "file_selection":
                    file_data = message_data.get("data", {})
                    selected_files = file_data.get("selected_files", [])
                    skip = file_data.get("skip", False)
                    
                    await improved_manager.handle_file_selection(session_id, selected_files, skip)
                    
                elif message_type == "error_choice":
                    choice = message_data.get("data", {}).get("choice", "")
                    logger.info(f"에러 처리 선택: {choice}")
                    
                    if choice == "다시 시도":
                        session_data = improved_manager.session_manager.get_session(session_id)
                        if session_data:
                            task_type = session_data.get("task_type")
                            state = session_data.get("agent_state", {})
                            
                            if task_type == "summary":
                                await improved_manager.adapter.adapt_summary_flow(session_id, state)
                            elif task_type == "generate_exam":
                                await improved_manager.adapter.adapt_exam_flow(session_id, state)
                            elif task_type == "schedule":
                                await improved_manager.adapter.adapt_schedule_flow(session_id, state)
                            else:
                                await improved_manager.send_error(session_id, "재시도할 작업을 찾을 수 없습니다.")
                        else:
                            await improved_manager.send_error(session_id, "세션 정보를 찾을 수 없습니다.")
                            
                    elif choice == "다른 작업 선택":
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
                    else:
                        await improved_manager.send_error(session_id, f"알 수 없는 선택: {choice}")
                    
                elif message_type == "ping":
                    await improved_manager.send_message(session_id, {
                        "type": "pong",
                        "session_id": session_id,
                        "timestamp": improved_manager.get_timestamp()
                    })

                elif message_type == "importance_input":
                    # 스케줄러 중요도 입력
                    await improved_manager.handle_importance_input(
                        session_id,
                        message_data["data"]
                    )
                elif message_type == "deadline_input":
                    # 스케줄러 마감일 입력  
                    await improved_manager.handle_deadline_input(
                        session_id,
                        message_data["data"]
                    )
                    
                else:
                    logger.warning(f"알 수 없는 메시지 타입: {message_type}")
                    await improved_manager.send_error(session_id, f"지원하지 않는 메시지 타입: {message_type}")
                    
            except WebSocketDisconnect:
                logger.info(f"WebSocket 정상 연결 해제: {session_id}")
                break
                
            except RuntimeError as e:
                if "disconnect message has been received" in str(e):
                    logger.info(f"WebSocket 이미 끊어짐: {session_id}")
                    break
                else:
                    logger.error(f"RuntimeError: {e}")
                    break
                    
            except Exception as receive_error:
                logger.error(f"메시지 수신 처리 오류: {str(receive_error)}", exc_info=True)
                
                # 📍 연결 상태 재확인
                try:
                    if websocket.application_state == WebSocketState.DISCONNECTED:
                        logger.info("WebSocket 연결 끊어짐 확인됨")
                        break
                    
                    # 연결이 유효하면 에러 메시지 전송 시도
                    await improved_manager.send_error(session_id, "메시지 처리 중 오류가 발생했습니다.")
                    
                except Exception as send_error:
                    logger.warning(f"에러 메시지 전송 실패: {send_error}")
                    break
                
    except WebSocketDisconnect:
        logger.info(f"WebSocket 연결 해제: {session_id}")
        
    except Exception as e:
        logger.error(f"WebSocket 전체 오류: {str(e)}", exc_info=True)
        
    finally:
        # 📍 안전한 정리 작업
        try:
            if session_id:
                await improved_manager.disconnect(session_id)
                logger.info(f"WebSocket 정리 완료: {session_id}")
        except Exception as cleanup_error:
            logger.error(f"정리 작업 오류: {cleanup_error}")


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
    
@router.get(
    "/improved-chat/sessions/{session_id}/history",
    summary="개선된 채팅 히스토리 조회",
    description="특정 세션의 모든 메시지 기록을 시간순으로 조회"
)
async def get_improved_chat_history(
    session_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """세션의 전체 채팅 기록 조회 (메시지 목록, 타임스탬프, 메타데이터 포함)"""
    try:
        # 세션 소유자 확인
        session_data = improved_manager.session_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        if current_user.id != int(session_data["user_id"]) and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        
        history = improved_manager.session_manager.get_chat_history(session_id)
        
        return {
            "session_id": session_id,
            "title": session_data.get("chat_title", "새 채팅"),
            "created_at": session_data.get("created_at"),
            "message_history": history,
            "message_count": len(history),
            "manager_type": "improved"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"개선된 채팅 히스토리 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="히스토리 조회 중 오류가 발생했습니다.")


@router.delete(
    "/improved-chat/sessions/{session_id}",
    summary="개선된 채팅 세션 삭제",
    description="특정 세션과 관련된 모든 데이터를 영구 삭제 (복구 불가)"
)
async def delete_improved_chat_session(
    session_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """세션 및 관련 메시지 완전 삭제 (DB에서 soft delete 처리)"""
    try:
        # 세션 소유자 확인
        session_data = improved_manager.session_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        if current_user.id != int(session_data["user_id"]) and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        
        # 세션 삭제 (실제로는 soft delete)
        success = improved_manager.session_manager.cleanup_session(session_id)
        
        if success:
            return {
                "session_id": session_id,
                "message": "개선된 채팅 세션이 삭제되었습니다.",
                "manager_type": "improved"
            }
        else:
            raise HTTPException(status_code=500, detail="세션 삭제에 실패했습니다.")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"개선된 채팅 세션 삭제 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="세션 삭제 중 오류가 발생했습니다.")


@router.patch(
    "/improved-chat/sessions/{session_id}/title",
    summary="개선된 채팅 제목 수정",
    description="사용자가 채팅방 이름을 직접 변경할 수 있도록 제목 업데이트"
)
async def update_improved_chat_title(
    session_id: str,
    title_data: dict,  # {"title": "새로운 제목"}
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """채팅방 제목 변경 (100자 제한, 특수문자 필터링)"""
    try:
        # 세션 소유자 확인
        session_data = improved_manager.session_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        if current_user.id != int(session_data["user_id"]) and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        
        new_title = title_data.get("title", "").strip()
        if not new_title:
            raise HTTPException(status_code=400, detail="제목을 입력해주세요.")
        
        # 제목 길이 제한 및 정제
        if len(new_title) > 100:
            new_title = new_title[:100]
        
        success = improved_manager.session_manager.update_session(session_id, {"chat_title": new_title})
        
        if success:
            return {
                "session_id": session_id,
                "title": new_title,
                "message": "개선된 채팅 제목이 변경되었습니다.",
                "manager_type": "improved"
            }
        else:
            raise HTTPException(status_code=500, detail="제목 변경에 실패했습니다.")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"개선된 채팅 제목 변경 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="제목 변경 중 오류가 발생했습니다.")


@router.get(
    "/improved-chat/sessions/{user_id}/stats",
    summary="개선된 채팅 사용 통계",
    description="사용자의 채팅 활동 통계 (총 세션 수, 메시지 수, 작업 타입별 분포)"
)
async def get_improved_chat_stats(
    user_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """사용자 채팅 통계 (세션 수, 메시지 수, 작업 타입별 분포, 최근 활동)"""
    try:
        # 권한 확인
        if current_user.id != int(user_id) and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        
        stats = improved_manager.session_manager.get_session_stats(user_id)
        stats["manager_type"] = "improved"
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"개선된 채팅 통계 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="통계 조회 중 오류가 발생했습니다.")


@router.post(
    "/improved-chat/sessions/{session_id}/reconnect",
    summary="개선된 채팅 세션 재연결",
    description="기존 세션에 다시 연결 (세션 만료 시간 연장, 상태 복원)"
)
async def reconnect_improved_chat_session(
    session_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """기존 세션 재활성화 (TTL 연장, 상태 검증, 메타데이터 갱신)"""
    try:
        # 세션 존재 확인
        session_data = improved_manager.session_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        # 세션 소유자 확인
        if current_user.id != int(session_data["user_id"]) and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        
        # TTL 연장
        improved_manager.session_manager.extend_session_ttl(session_id)
        
        return {
            "session_id": session_id,
            "title": session_data.get("chat_title", "새 채팅"),
            "task_type": session_data.get("task_type", "qa"),
            "waiting_for": session_data.get("waiting_for"),
            "message": "개선된 세션에 재연결되었습니다.",
            "manager_type": "improved"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"개선된 세션 재연결 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="재연결 중 오류가 발생했습니다.")


@router.get(
    "/improved-chat/sessions/{session_id}/status",
    summary="개선된 채팅 세션 상태 조회",  
    description="현재 세션의 작업 진행 상황 및 대기 중인 입력 확인"
)
async def get_improved_chat_session_status(
    session_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """세션 현재 상태 조회 (작업 타입, 대기 입력, 진행 단계 등)"""
    try:
        # 세션 소유자 확인
        session_data = improved_manager.session_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        if current_user.id != int(session_data["user_id"]) and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        
        return {
            "session_id": session_id,
            "task_type": session_data.get("task_type", "qa"),
            "waiting_for": session_data.get("waiting_for"),
            "current_request_type": session_data.get("current_request_type"),
            "created_at": session_data.get("created_at"),
            "is_active": session_id in improved_manager.active_connections,
            "manager_type": "improved"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"개선된 세션 상태 조회 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="상태 조회 중 오류가 발생했습니다.")


@router.post(
    "/improved-chat/sessions/{session_id}/reset",
    summary="개선된 채팅 세션 초기화",
    description="현재 진행 중인 작업을 중단하고 QA 모드로 초기화"
)
async def reset_improved_chat_session(
    session_id: str,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """세션 상태 초기화 (진행 중인 작업 중단, QA 모드로 변경)"""
    try:
        # 세션 소유자 확인
        session_data = improved_manager.session_manager.get_session(session_id)
        if not session_data:
            raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
        
        if current_user.id != int(session_data["user_id"]) and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="권한이 없습니다.")
        
        # 세션 상태 초기화
        reset_data = {
            "task_type": "qa",
            "waiting_for": None,
            "current_request_type": None,
            "agent_state": {}
        }
        
        success = improved_manager.session_manager.update_session(session_id, reset_data)
        
        if success:
            return {
                "session_id": session_id,
                "task_type": "qa",
                "message": "세션이 초기화되었습니다. 새로운 작업을 시작할 수 있습니다.",
                "manager_type": "improved"
            }
        else:
            raise HTTPException(status_code=500, detail="세션 초기화에 실패했습니다.")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"개선된 세션 초기화 오류: {str(e)}")
        raise HTTPException(status_code=500, detail="세션 초기화 중 오류가 발생했습니다.")