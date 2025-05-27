# app/api/v1/websocket/handlers.py - 모든 작업 타입 핸들러

import asyncio
import json
from typing import Dict, List, Any
from langchain_core.messages import HumanMessage, AIMessage
import logging
import os

logger = logging.getLogger(__name__)

class TaskHandlers:
    """모든 작업 타입에 대한 핸들러 모음"""
    
    def __init__(self, websocket_manager):
        self.manager = websocket_manager
    
    # ==================== 파일 선택 처리 ====================
    
    async def handle_file_selection(self, session_id: str, selected_files: list, skip: bool = False):
        """파일 선택 처리"""
        try:
            session_data = self.manager.session_manager.get_session(session_id)
            if not session_data:
                await self.manager.send_error(session_id, "세션을 찾을 수 없습니다.")
                return

            task_type = session_data.get("task_type")
            request_type = session_data.get("current_request_type")
            
            if task_type == "summary":
                await self.handle_summary_file_selection(session_id, selected_files, session_data)
            elif task_type == "generate_exam":
                await self.handle_exam_file_selection(session_id, selected_files, skip, session_data)
            elif task_type == "schedule":
                await self.handle_scheduler_file_selection(session_id, selected_files, session_data)
                
        except Exception as e:
            logger.error(f"파일 선택 처리 오류: {str(e)}")
            await self.manager.send_error(session_id, "파일 처리 중 오류가 발생했습니다.")

    # ==================== 요약 처리 ====================
    
    async def handle_summary_file_selection(self, session_id: str, selected_files: list, session_data: dict):
        """요약용 파일 선택 처리"""
        valid_files = await self.validate_file_paths(session_data["user_id"], selected_files)
        if not valid_files:
            await self.manager.send_error(session_id, "유효한 파일을 선택해주세요.")
            return

        await self.execute_summary(session_id, valid_files[0], session_data)
    
    async def execute_summary(self, session_id: str, file_path: str, session_data: dict):
        """요약 실행"""
        try:
            current_state = session_data["agent_state"]
            
            # 파일 경로 설정
            current_state["pdf_path"] = file_path
            current_state["folder"] = self.extract_folder_from_path(file_path)
            
            await self.manager.send_status(session_id, "processing", "문서를 분석하고 있습니다...", 20)
            
            # 요약 에이전트 실행
            steps = [
                ("get_related_pdf", "관련 문서를 가져오고 있습니다...", 40),
                ("pdf_parsing", "문서를 파싱하고 있습니다...", 60),
                ("summary_pdf", "요약을 생성하고 있습니다...", 80),
                ("save_file", "결과를 저장하고 있습니다...", 100)
            ]
            
            result = current_state
            for step_name, message, progress in steps:
                await self.manager.send_status(session_id, "processing", message, progress)
                result = await self.manager.run_agent_step(result, step_name)
            # ✅ 여기서 문제 content 생성해 넣기
            result["result"] = "\n".join(result.get("problems", []))  # 🔥 핵심 수                
            
            # 결과 전송
            summary_content = result.get("result", "요약을 생성할 수 없습니다.")
            
            await self.manager.send_message(session_id, {
                "type": "result",
                "session_id": session_id,
                "data": {
                    "task_type": "summary",
                    "content": summary_content,
                    "file_path": result.get("saved_path")
                },
                "timestamp": self.manager.get_timestamp()
            })
            
            # QA 모드로 전환
            self.manager.session_manager.update_session(session_id, {
                "task_type": "qa",
                "waiting_for": None,
                "current_request_type": None,
                "agent_state": result
            })
            
            await self.manager.send_message(session_id, {
                "type": "ai_response",
                "session_id": session_id,
                "data": {
                    "message": "요약이 완료되었습니다! 추가로 궁금한 것이 있으시면 언제든 질문해주세요.",
                    "task_type": "qa",
                    "is_final": False
                },
                "timestamp": self.manager.get_timestamp()
            })
            
        except Exception as e:
            logger.error(f"요약 실행 오류: {str(e)}")
            await self.manager.send_error(session_id, "요약 생성 중 오류가 발생했습니다.")

    # ==================== 시험 문제 생성 처리 ====================
    
    async def handle_exam_file_selection(self, session_id: str, selected_files: list, skip: bool, session_data: dict):
        """시험 문제 생성용 파일 선택 처리"""
        request_type = session_data.get("current_request_type")

        # 유효한 파일 경로만 필터링
        valid_files = await self.validate_file_paths(session_data["user_id"], selected_files)
        if not valid_files and not skip:
            await self.manager.send_error(session_id, "유효한 파일을 선택해주세요.")
            return

        if request_type == "previous_exam":
            if skip:
                # 기출문제 스킵 - 학습자료 선택으로 이동
                await self.request_study_material_selection(session_id)
            else:
                # 기출문제 선택됨 - 분석 후 학습자료 선택
                await self.analyze_previous_exams(session_id, valid_files, session_data)
        elif request_type == "study_material":
            # 학습자료 선택됨 - 시험문제 생성
            await self.execute_exam_generation(session_id, valid_files[0], session_data)

    async def request_study_material_selection(self, session_id: str):
        """학습자료 선택 요청"""
        try:
            session_data = self.manager.session_manager.get_session(session_id)
            user_id = session_data["user_id"]
            available_files = await self.manager.get_user_files(user_id)
            
            await self.manager.send_message(session_id, {
                "type": "file_request",
                "session_id": session_id,
                "data": {
                    "message": "시험 범위가 될 학습 자료를 선택해주세요",
                    "request_type": "study_material",
                    "multiple": False,
                    "optional": False,
                    "available_files": available_files
                },
                "timestamp": self.manager.get_timestamp()
            })
            
            self.manager.session_manager.update_session(session_id, {
                "current_request_type": "study_material",
                "exam_step": "study_material_selection"
            })
            
        except Exception as e:
            logger.error(f"학습자료 선택 요청 오류: {str(e)}")
            await self.manager.send_error(session_id, "학습자료 선택을 요청할 수 없습니다.")

    async def analyze_previous_exams(self, session_id: str, exam_files: list, session_data: dict):
        """기출문제 분석"""
        try:
            current_state = session_data["agent_state"]
            current_state["previous_exam_path"] = exam_files
            
            await self.manager.send_status(session_id, "processing", "기출문제를 분석하고 있습니다...", 30)
            
            # 기출문제 분석 실행
            result = await self.manager.run_agent_step(current_state, "analyze_previous_exam")
            
            # 분석 완료 후 학습자료 선택 요청
            self.manager.session_manager.update_session(session_id, {"agent_state": result})
            await self.request_study_material_selection(session_id)
            
        except Exception as e:
            logger.error(f"기출문제 분석 오류: {str(e)}")
            await self.manager.send_error(session_id, "기출문제 분석 중 오류가 발생했습니다.")

    async def execute_exam_generation(self, session_id: str, study_file: str, session_data: dict):
        """시험문제 생성 실행"""
        try:
            current_state = session_data["agent_state"]
            current_state["pdf_path"] = study_file
            current_state["folder"] = self.extract_folder_from_path(study_file)
            
            steps = [
                ("get_concept_for_exam", "출제 개념을 추출하고 있습니다...", 60),
                ("refine_problems", "시험문제를 생성하고 있습니다...", 100)
            ]
            
            result = current_state
            for step_name, message, progress in steps:
                await self.manager.send_status(session_id, "processing", message, progress)
                result = await self.manager.run_agent_step(result, step_name)
            
            # 결과 전송
            exam_content = result.get("result", "시험문제를 생성할 수 없습니다.")
            
            await self.manager.send_message(session_id, {
                "type": "result",
                "session_id": session_id,
                "data": {
                    "task_type": "exam",
                    "content": exam_content,
                    "file_path": result.get("file_path") or "problem.md"
                },
                "timestamp": self.manager.get_timestamp()
            })
            
            # QA 모드로 전환
            self.manager.session_manager.update_session(session_id, {
                "task_type": "qa",
                "waiting_for": None,
                "current_request_type": None,
                "agent_state": result,
                "exam_step": "study_material_selected"
            })
            
            await self.manager.send_message(session_id, {
                "type": "ai_response",
                "session_id": session_id,
                "data": {
                    "message": "시험문제 생성이 완료되었습니다! 문제에 대해 궁금한 것이 있으시면 언제든 질문해주세요.",
                    "task_type": "qa",
                    "is_final": False
                },
                "timestamp": self.manager.get_timestamp()
            })
            
        except Exception as e:
            logger.error(f"시험문제 생성 오류: {str(e)}")
            await self.manager.send_error(session_id, "시험문제 생성 중 오류가 발생했습니다.")

    # ==================== 스케줄러 처리 ====================
    
    async def handle_scheduler_file_selection(self, session_id: str, selected_files: list, session_data: dict):
        """스케줄러용 파일 선택 처리"""
        valid_files = await self.validate_file_paths(session_data["user_id"], selected_files)
        if not valid_files:
            await self.manager.send_error(session_id, "유효한 학습 자료를 선택해주세요.")
            return

        # 선택된 파일들에서 과목명 추출
        subjects = self.extract_unique_subjects(selected_files)
        
        scheduler_data = session_data.get("scheduler_data", {})
        scheduler_data.update({
            "selected_materials": selected_files,
            "subjects": subjects
        })
        
        # 중요도 입력 요청
        await self.request_importance_input(session_id, subjects, scheduler_data)

    async def request_importance_input(self, session_id: str, subjects: list, scheduler_data: dict):
        """중요도 입력 요청"""
        try:
            subject_list = "\n".join([f"- {subject}" for subject in subjects])
            message = f"각 과목의 중요도를 1-5로 입력해주세요:\n{subject_list}\n\n예시: 정보보호: 5, 네트워크: 3, 운영체제: 4"
            
            await self.manager.send_message(session_id, {
                "type": "ai_response",
                "session_id": session_id,
                "data": {
                    "message": message,
                    "task_type": "schedule",
                    "is_final": False,
                    "input_required": "importance"
                },
                "timestamp": self.manager.get_timestamp()
            })
            
            self.manager.session_manager.update_session(session_id, {
                "scheduler_step": "importance_input",
                "scheduler_data": scheduler_data,
                "waiting_for": "importance_input"
            })
            
        except Exception as e:
            logger.error(f"중요도 입력 요청 오류: {str(e)}")
            await self.manager.send_error(session_id, "중요도 입력을 요청할 수 없습니다.")

    async def handle_importance_input(self, session_id: str, importance_data: dict):
        """중요도 입력 처리"""
        try:
            session_data = self.manager.session_manager.get_session(session_id)
            scheduler_data = session_data.get("scheduler_data", {})
            
            scheduler_data["importance"] = importance_data
            subjects = scheduler_data.get("subjects", [])
            
            # 마감일 입력 요청
            await self.request_deadline_input(session_id, subjects, scheduler_data)
            
        except Exception as e:
            logger.error(f"중요도 입력 처리 오류: {str(e)}")
            await self.manager.send_error(session_id, "중요도 처리 중 오류가 발생했습니다.")

    async def request_deadline_input(self, session_id: str, subjects: list, scheduler_data: dict):
        """마감일 입력 요청"""
        try:
            subject_list = "\n".join([f"- {subject}" for subject in subjects])
            message = f"각 과목의 시험 날짜를 입력해주세요:\n{subject_list}\n\n예시: 정보보호: 2025-06-01, 네트워크: 2025-06-03, 운영체제: 2025-06-05"
            
            await self.manager.send_message(session_id, {
                "type": "ai_response",
                "session_id": session_id,
                "data": {
                    "message": message,
                    "task_type": "schedule",
                    "is_final": False,
                    "input_required": "deadline"
                },
                "timestamp": self.manager.get_timestamp()
            })
            
            self.manager.session_manager.update_session(session_id, {
                "scheduler_step": "deadline_input",
                "scheduler_data": scheduler_data,
                "waiting_for": "deadline_input"
            })
            
        except Exception as e:
            logger.error(f"마감일 입력 요청 오류: {str(e)}")
            await self.manager.send_error(session_id, "마감일 입력을 요청할 수 없습니다.")

    async def handle_deadline_input(self, session_id: str, deadline_data: dict):
        """마감일 입력 처리 및 스케줄 생성"""
        try:
            session_data = self.manager.session_manager.get_session(session_id)
            scheduler_data = session_data.get("scheduler_data", {})
            
            scheduler_data["deadlines"] = deadline_data
            
            # 스케줄 생성 실행
            await self.execute_schedule_generation(session_id, scheduler_data, session_data)
            
        except Exception as e:
            logger.error(f"마감일 입력 처리 오류: {str(e)}")
            await self.manager.send_error(session_id, "마감일 처리 중 오류가 발생했습니다.")

    async def execute_schedule_generation(self, session_id: str, scheduler_data: dict, session_data: dict):
        """스케줄 생성 실행"""
        try:
            current_state = session_data["agent_state"]
            
            # 스케줄러 데이터를 상태에 반영
            current_state.update({
                "subjects": scheduler_data["subjects"],
                "importance": scheduler_data["importance"],
                "deadlines": scheduler_data["deadlines"],
                "selected_files": scheduler_data["selected_materials"]
            })
            
            await self.manager.send_status(session_id, "processing", "학습 계획을 생성하고 있습니다...", 50)
            
            # 스케줄 생성 실행
            steps = [
                ("get_all_document", "문서를 분석하고 있습니다...", 70),
                ("make_plans", "학습 계획을 수립하고 있습니다...", 90),
                ("save_plan", "계획을 저장하고 있습니다...", 100)
            ]
            
            result = current_state
            for step_name, message, progress in steps:
                await self.manager.send_status(session_id, "processing", message, progress)
                result = await self.manager.run_agent_step(result, step_name)
            
            # 결과 전송
            schedule_content = result.get("schedule", {})
            
            file_path = result.get("schedule_file_path") or "unknown_schedule_path.json"

            await self.manager.send_message(session_id, {
                "type": "result",
                "session_id": session_id,
                "data": {
                    "task_type": "scheduler",
                    "content": schedule_content,
                    "file_path": file_path
                },
                "timestamp": self.manager.get_timestamp()
            })
            
            # QA 모드로 전환
            self.manager.session_manager.update_session(session_id, {
                "task_type": "qa",
                "waiting_for": None,
                "current_request_type": None,
                "agent_state": result,
                "scheduler_step": "schedule_generated"
            })
            
            await self.manager.send_message(session_id, {
                "type": "ai_response",
                "session_id": session_id,
                "data": {
                    "message": "학습 계획이 완성되었습니다! 계획에 대해 궁금한 것이 있으시면 언제든 질문해주세요.",
                    "task_type": "qa",
                    "is_final": False
                },
                "timestamp": self.manager.get_timestamp()
            })
            
        except Exception as e:
            logger.error(f"스케줄 생성 오류: {str(e)}")
            await self.manager.send_error(session_id, "학습 계획 생성 중 오류가 발생했습니다.")

    # ==================== 유틸리티 함수 ====================
    
    def extract_folder_from_path(self, file_path: str) -> str:
        """파일 경로에서 폴더명 추출"""
        import os
        return os.path.dirname(file_path).split('/')[-1] if '/' in file_path else "default"
    
    def extract_subject_from_filename(self, filepath: str) -> str:
        name = os.path.basename(filepath).split('.')[0]
        return name.replace('_', ' ').replace('-', ' ').strip()

    async def process_importance_input(self, session_id: str, message: str, scheduler_data: dict):
        """중요도 입력 텍스트 파싱"""
        try:
            # "정보보호: 5, 네트워크: 3" 형태의 입력 파싱
            importance = {}
            parts = message.split(',')
            
            for part in parts:
                if ':' in part:
                    subject, value = part.split(':', 1)
                    subject = subject.strip()
                    try:
                        importance[subject] = int(value.strip())
                    except ValueError:
                        continue
            
            if importance:
                await self.handle_importance_input(session_id, importance)
            else:
                await self.manager.send_error(session_id, "올바른 형식으로 입력해주세요. 예: 정보보호: 5, 네트워크: 3")
                
        except Exception as e:
            logger.error(f"중요도 입력 파싱 오류: {str(e)}")
            await self.manager.send_error(session_id, "중요도 입력 처리 중 오류가 발생했습니다.")

    async def process_deadline_input(self, session_id: str, message: str, scheduler_data: dict):
        """마감일 입력 텍스트 파싱"""
        try:
            # "정보보호: 2025-06-01, 네트워크: 2025-06-03" 형태의 입력 파싱
            deadlines = {}
            parts = message.split(',')
            
            for part in parts:
                if ':' in part:
                    subject, date_str = part.split(':', 1)
                    subject = subject.strip()
                    date_str = date_str.strip()
                    
                    # 날짜 형식 검증
                    try:
                        from datetime import datetime
                        datetime.strptime(date_str, '%Y-%m-%d')
                        deadlines[subject] = date_str
                    except ValueError:
                        continue
            
            if deadlines:
                await self.handle_deadline_input(session_id, deadlines)
            else:
                await self.manager.send_error(session_id, "올바른 날짜 형식으로 입력해주세요. 예: 정보보호: 2025-06-01, 네트워크: 2025-06-03")
                
        except Exception as e:
            logger.error(f"마감일 입력 파싱 오류: {str(e)}")
            await self.manager.send_error(session_id, "마감일 입력 처리 중 오류가 발생했습니다.")

    async def validate_file_paths(self, user_id: str, selected_files: list) -> list:
        """S3 또는 로컬에서 유효한 파일 경로만 반환"""
        all_files = await self.manager.get_user_files(user_id)
        valid_paths = {f["path"] for f in all_files}
        return [f for f in selected_files if f in valid_paths]
    
    def extract_unique_subjects(self, files: list) -> list:
        """파일명으로부터 중복되지 않는 고유 과목명 리스트 생성"""
        subjects, seen = [], set()
        for f in files:
            subject = self.extract_subject_from_filename(f)
            base = subject
            i = 1
            while subject in seen:
                subject = f"{base}_{i}"
                i += 1
            subjects.append(subject)
            seen.add(subject)
        return subjects