# app/services/pdf_agent/adapters/websocket_adapter.py
"""
기존 Graph/Node를 WebSocket 환경에서 사용할 수 있도록 어댑터 패턴 적용
input() 기반 → 상태 기반 요청으로 변환
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from langchain_core.messages import HumanMessage, AIMessage

from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.tools import get_initial_state
from app.services.pdf_agent.graphs.main import intergrate_graph
from app.services.s3_file_service import S3StorageManager
from app.core.config import settings

logger = logging.getLogger(__name__)

class WebSocketNodeAdapter:
    """기존 nodes를 WebSocket에서 사용할 수 있도록 어댑터"""
    
    def __init__(self, websocket_manager):
        self.manager = websocket_manager
        self.agent_graph = intergrate_graph()
        self.s3_manager = S3StorageManager()
    
    # ==================== Summary 어댑터 ====================
    
    async def adapt_summary_flow(self, session_id: str, state: AgentState) -> str:
        """요약 플로우 어댑터"""
        try:
            # 1. 파일 선택 필요한지 확인
            if not state.get("pdf_path"):
                await self._request_file_selection(
                    session_id,
                    "어떤 자료를 요약해드릴까요?",
                    request_type="summary_target",
                    multiple=False
                )
                return "waiting_for_file"
            
            # 2. 파일 경로가 있으면 요약 실행
            await self.manager.send_status(session_id, "processing", "요약을 생성하고 있습니다...", 20)
            
            # 기존 summary graph 실행 (input() 우회)
            result = await self._run_summary_nodes(state)
            
            # 3. 결과 전송
            await self.manager.send_message(session_id, {
                "type": "result",
                "session_id": session_id,
                "data": {
                    "task_type": "summary",
                    "content": result.get("result", "요약 생성 실패"),
                    "file_path": result.get("saved_path")
                },
                "timestamp": self.manager.get_timestamp()
            })
            
            return "completed"
            
        except Exception as e:
            logger.error(f"Summary 어댑터 오류: {str(e)}", exc_info=True)
            await self.manager.send_error(session_id, f"요약 생성 중 오류: {str(e)}")
            return "error"
    
    async def _run_summary_nodes(self, state: AgentState) -> Dict[str, Any]:
        """Summary nodes 실행 (input() 우회)"""
        try:
            from app.services.pdf_agent.nodes.summary import (
                get_related_pdf, pdf_parsing, summary_pdf, 
                get_need_to_explain, explain, add_explaination, save_file
            )
            
            # 순차적으로 summary 단계 실행
            result = state
            result = get_related_pdf(result)
            result = pdf_parsing(result)  
            result = summary_pdf(result)
            result = get_need_to_explain(result)
            result = explain(result)
            result = add_explaination(result)
            result = save_file(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Summary nodes 실행 오류: {str(e)}", exc_info=True)
            raise
    
    # ==================== Exam 어댑터 ====================
    
    async def adapt_exam_flow(self, session_id: str, state: AgentState) -> str:
        """시험 문제 생성 플로우 어댑터"""
        try:
            exam_step = state.get("exam_step", "start")
            logger.info(f"Exam 플로우 단계: {exam_step}")
            
            if exam_step == "start":
                # 기출문제 선택 요청
                await self._request_file_selection(
                    session_id,
                    "기출문제가 있나요? (선택사항)",
                    request_type="previous_exam",
                    multiple=True,
                    optional=True
                )
                return "waiting_for_previous_exam"
                
            elif exam_step == "previous_exam_selected":
                # 학습자료 선택 요청
                await self._request_file_selection(
                    session_id,
                    "시험 범위가 될 학습 자료를 선택해주세요",
                    request_type="study_material", 
                    multiple=False,
                    optional=False
                )
                return "waiting_for_study_material"
                
            elif exam_step == "study_material_selected":
                # 시험문제 생성 실행
                await self.manager.send_status(session_id, "processing", "시험문제를 생성하고 있습니다...", 50)
                result = await self._run_exam_nodes(state)
                
                await self.manager.send_message(session_id, {
                    "type": "result", 
                    "session_id": session_id,
                    "data": {
                        "task_type": "exam",
                        "content": result.get("problems", "문제 생성 실패"),
                        "file_path": result.get("file_path", "problem.md")
                    },
                    "timestamp": self.manager.get_timestamp()
                })
                return "completed"
                
        except Exception as e:
            logger.error(f"Exam 어댑터 오류: {str(e)}", exc_info=True)
            await self.manager.send_error(session_id, f"시험문제 생성 중 오류: {str(e)}")
            return "error"
    
    async def _run_exam_nodes(self, state: AgentState) -> Dict[str, Any]:
        """Exam nodes 실행 (input() 우회)"""
        try:
            from app.services.pdf_agent.nodes.exam import (
                get_all_files, get_concept_for_exam, refine_problems, save_exam
            )
            
            result = state
            result = get_all_files(result)
            result = get_concept_for_exam(result)
            result = refine_problems(result)
            result = save_exam(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Exam nodes 실행 오류: {str(e)}", exc_info=True)
            raise
    
    # ==================== Schedule 어댑터 ====================
    
    async def adapt_schedule_flow(self, session_id: str, state: AgentState) -> str:
        """스케줄러 플로우 어댑터"""
        try:
            schedule_step = state.get("scheduler_step", "start")
            logger.info(f"Schedule 플로우 단계: {schedule_step}")

            # 전체 상태 로그 (민감한 정보 제외)
            state_keys = list(state.keys())
            logger.info(f"현재 state 키들: {state_keys}")
            
            if schedule_step == "start":
                # 학습자료 다중 선택 요청
                await self._request_file_selection(
                    session_id,
                    "공부할 자료들을 선택해주세요 (여러 개 선택 가능)",
                    request_type="scheduler_materials",
                    multiple=True,
                    optional=False
                )
                return "waiting_for_materials"
                
            elif schedule_step == "materials_selected":
                # 중요도 입력 요청
                subjects = state.get("subjects", [])
                await self._request_additional_input(
                    session_id,
                    f"각 과목의 중요도를 1-5로 입력해주세요:\n{', '.join(subjects)}\n\n예: {subjects[0]}: 5",
                    input_type="importance"
                )
                return "waiting_for_importance"
                
            elif schedule_step == "importance_set":
                # 마감일 입력 요청
                subjects = state.get("subjects", [])
                await self._request_additional_input(
                    session_id,
                    f"각 과목의 시험 날짜를 입력해주세요:\n{', '.join(subjects)}\n\n예: {subjects[0]}: 2025-06-15",
                    input_type="deadlines"
                )
                return "waiting_for_deadlines"
                
            elif schedule_step == "deadlines_set":
                # 스케줄 생성 실행
                await self.manager.send_status(session_id, "processing", "학습 계획을 생성하고 있습니다...", 50)
                result = await self._run_schedule_nodes(state)
                
                await self.manager.send_message(session_id, {
                    "type": "result",
                    "session_id": session_id, 
                    "data": {
                        "task_type": "scheduler",
                        "content": result.get("schedule", {}),
                        "file_path": result.get("schedule_file_path", "schedule.json")
                    },
                    "timestamp": self.manager.get_timestamp()
                })
                return "completed"
                
        except Exception as e:
            logger.error(f"Schedule 어댑터 오류: {str(e)}", exc_info=True)
            await self.manager.send_error(session_id, f"학습 계획 생성 중 오류: {str(e)}")
            return "error"
    
    async def _run_schedule_nodes(self, state: AgentState) -> Dict[str, Any]:
        """Schedule nodes 실행 (input() 우회)"""
        try:
            from app.services.pdf_agent.nodes.scheduler import (
                get_all_document, define_final_index, make_plans, save_plan
            )
            
            result = state
            result = get_all_document(result)
            result = define_final_index(result)
            result = make_plans(result)
            result = save_plan(result)
            
            return result
            
        except Exception as e:
            logger.error(f"Schedule nodes 실행 오류: {str(e)}", exc_info=True)
            raise
    
    # ==================== QA 어댑터 ====================
    
    async def adapt_qa_flow(self, session_id: str, state: AgentState, user_query: str) -> str:
        """QA 플로우 어댑터 (즉시 응답)"""
        try:
            from app.services.pdf_agent.nodes.qa_system import start_point_of_qa_system
            
            # 사용자 메시지를 상태에 추가
            messages = state.get("messages", [])
            messages.append(HumanMessage(content=user_query))
            state["messages"] = messages
            
            # QA 실행
            result = start_point_of_qa_system(state)
            
            # 응답 추출
            response_content = result.get("last_assistant_response", "답변을 생성할 수 없습니다.")
            
            await self.manager.send_message(session_id, {
                "type": "ai_response",
                "session_id": session_id,
                "data": {
                    "message": response_content,
                    "task_type": "qa",
                    "is_final": False
                },
                "timestamp": self.manager.get_timestamp()
            })
            
            return "completed"
            
        except Exception as e:
            logger.error(f"QA 어댑터 오류: {str(e)}", exc_info=True)
            await self.manager.send_error(session_id, f"답변 생성 중 오류: {str(e)}")
            return "error"
    
    # ==================== 헬퍼 메서드들 ====================
    
    async def _request_file_selection(
        self, 
        session_id: str, 
        message: str, 
        request_type: str,
        multiple: bool = False,
        optional: bool = False
    ):
        """파일 선택 요청"""
        try:
            session_data = self.manager.session_manager.get_session(session_id)
            user_id = session_data["user_id"]
            
            # S3에서 사용자 파일 목록 조회
            available_files = await self._get_user_files(user_id)
            
            await self.manager.send_message(session_id, {
                "type": "file_request",
                "session_id": session_id,
                "data": {
                    "message": message,
                    "request_type": request_type,
                    "multiple": multiple,
                    "optional": optional,
                    "available_files": available_files
                },
                "timestamp": self.manager.get_timestamp()
            })
            
            # 세션 상태 업데이트
            self.manager.session_manager.update_session(session_id, {
                "waiting_for": "file_selection",
                "current_request_type": request_type
            })
            
        except Exception as e:
            logger.error(f"파일 선택 요청 오류: {str(e)}", exc_info=True)
            await self.manager.send_error(session_id, "파일 목록을 불러올 수 없습니다.")
    
    async def _request_additional_input(
        self,
        session_id: str,
        message: str, 
        input_type: str
    ):
        """추가 입력 요청"""
        try:
            await self.manager.send_message(session_id, {
                "type": "ai_response",
                "session_id": session_id,
                "data": {
                    "message": message,
                    "task_type": "schedule",
                    "is_final": False,
                    "input_required": input_type
                },
                "timestamp": self.manager.get_timestamp()
            })
            
            self.manager.session_manager.update_session(session_id, {
                "waiting_for": f"{input_type}_input"
            })
            
        except Exception as e:
            logger.error(f"추가 입력 요청 오류: {str(e)}", exc_info=True)
            await self.manager.send_error(session_id, "입력 요청을 처리할 수 없습니다.")
    
    async def _get_user_files(self, user_id: str) -> List[Dict[str, Any]]:
        """사용자 파일 목록 조회 (S3 기반)"""
        try:
            folders = self.s3_manager.list_folders(int(user_id))
            results = []
            
            for folder in folders:
                files = self.s3_manager.list_files(int(user_id), folder.name)
                for file_name in files:
                    if file_name.lower().endswith(".pdf"):
                        # S3 URL 생성
                        s3_url = f"https://{self.s3_manager.bucket_name}.s3.amazonaws.com/users/{user_id}/{folder.name}/{file_name}"
                        results.append({
                            "name": file_name,
                            "folder": folder.name,
                            "path": s3_url,  # S3 URL로 반환
                            "type": "pdf"
                        })
            
            logger.info(f"사용자 {user_id} 파일 목록: {len(results)}개")
            return results
            
        except Exception as e:
            logger.error(f"파일 목록 조회 실패: {str(e)}", exc_info=True)
            return []
    
    def _resolve_s3_to_local_path(self, s3_path: str, user_id: str) -> str:
        """S3 경로를 ChromaDB에서 검색할 수 있는 형태로 변환"""
        # ChromaDB는 컨테이너 내부에 저장되므로 사용자별 경로 반환
        return f"{settings.CHROMADB_STORAGE_PATH}/{user_id}"