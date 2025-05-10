# app/services/pdf_agent/ai_service.py

import os
from typing import Dict, Any, List
import logging
from dotenv import load_dotenv
from .graphs.main import intergrate_graph
from .states import AgentState

logger = logging.getLogger(__name__)
load_dotenv()

class PDFAIService:
    """
    PDF AI 서비스 - LangGraph 워크플로우를 래핑하는 클래스
    """
    
    def __init__(self):
        """서비스 초기화"""
        try:
            self.chain = intergrate_graph()
            logger.info("PDF AI 서비스 초기화 완료")
        except Exception as e:
            logger.error(f"PDF AI 서비스 초기화 실패: {str(e)}", exc_info=True)
            self.chain = None
    
    def process_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """
        PDF 처리 워크플로우 실행
        
        Args:
            pdf_path: 처리할 PDF 파일 경로
            
        Returns:
            처리 결과 (요약, 학습 자료, 문제 등)
        """
        try:
            if not os.path.exists(pdf_path):
                return {"success": False, "error": f"파일이 존재하지 않습니다: {pdf_path}"}
                
            # 초기 상태 설정 (app.py 참고)
            initial_state = {
                "pdf_path": pdf_path,
                "pdf_step": 0,
                "summaries": "",
                "explain_step": 0,
                "pdfs": [],
                "messages": [],
                "result": "",
                "need_to_explain": {},
                "previous_exam_problems": [],
                "analysis_of_exam_writers": ""
            }
            
            # 워크플로우 실행
            final_state = self.chain.invoke(initial_state, config={"recursion_limit": 200})
            
            # 결과 반환
            return {
                "success": True,
                "result": final_state["result"],
                "pdf_path": pdf_path
            }
            
        except Exception as e:
            logger.error(f"PDF 처리 실패: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "pdf_path": pdf_path
            }
    
    def generate_exam(self, file_path: str, num_questions: int = 5) -> Dict[str, Any]:
        """
        학습 내용 기반 시험 문제 생성
        
        Args:
            file_path: 시험 문제 생성용 PDF 파일 경로
            num_questions: 생성할 문제 수
            
        Returns:
            시험 문제
        """
        try:
            from .nodes.exam import analyze_exam, generate_exam, get_exam_document
            
            # exam.py의 함수 호출
            documents = get_exam_document(file_path)
            analysis = analyze_exam(documents)
            questions = generate_exam(analysis, num_questions)
            
            return {
                "success": True,
                "questions": questions
            }
        
        except Exception as e:
            logger.error(f"시험 문제 생성 실패: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }