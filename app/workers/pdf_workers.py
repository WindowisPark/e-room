import logging
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.workers.task_manager import TaskManager
from app.services.pdf_agent.ai_agent import PDFAgent
from app.services.notification_service import send_notification

logger = logging.getLogger(__name__)
task_manager = TaskManager()

# 비동기 작업 핸들러 함수들
# 각 함수는 작업 큐에서 실행되며, 작업 진행 상태 업데이트 및 완료 알림 발송

async def process_pdf_summarize(db: Session, document_id: int, level: str, user_id: int) -> Dict[str, Any]:
    """
    PDF 요약 비동기 처리 핸들러
    
    Args:
        db: 데이터베이스 세션
        document_id: 문서 ID
        level: 요약 수준
        user_id: 사용자 ID
        
    Returns:
        처리 결과
    """
    job_id = f"summarize_{document_id}_{user_id}"
    
    try:
        # 진행 상태 업데이트
        task_manager.update_job_progress(job_id, 10, "PDF 파싱 중...")
        
        # 요약 생성 (기본 구현)
        result = await PDFAgent.summarize(db, document_id, level)
        
        # 진행 상태 업데이트
        task_manager.update_job_progress(job_id, 100, "요약 생성 완료")
        
        # 작업 완료 알림
        if result.get("success"):
            await send_notification(
                db=db,
                user_id=user_id,
                type="system",
                message=f"PDF 요약이 생성되었습니다: {result.get('document_name')}",
                link=f"/pdf-agent/{document_id}/summary"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"PDF 요약 처리 실패: {str(e)}", exc_info=True)
        
        # 오류 알림
        await send_notification(
            db=db,
            user_id=user_id,
            type="system",
            message=f"PDF 요약 중 오류가 발생했습니다: {str(e)}",
            link=f"/pdf-agent/{document_id}"
        )
        
        # 작업 상태 업데이트
        task_manager.update_job_progress(job_id, 100, f"오류 발생: {str(e)}")
        
        return {"success": False, "error": str(e)}

async def process_pdf_questions(db: Session, document_id: int, count: int, user_id: int) -> Dict[str, Any]:
    """
    PDF 문제 생성 비동기 처리 핸들러
    
    Args:
        db: 데이터베이스 세션
        document_id: 문서 ID
        count: 문제 수
        user_id: 사용자 ID
        
    Returns:
        처리 결과
    """
    job_id = f"questions_{document_id}_{user_id}"
    
    try:
        # 진행 상태 업데이트
        task_manager.update_job_progress(job_id, 10, "PDF 파싱 중...")
        
        # 문제 생성 (기본 구현)
        result = await PDFAgent.generate_questions(db, document_id, count)
        
        # 진행 상태 업데이트
        task_manager.update_job_progress(job_id, 100, "문제 생성 완료")
        
        # 작업 완료 알림
        if result.get("success"):
            await send_notification(
                db=db,
                user_id=user_id,
                type="system",
                message=f"PDF 문제가 생성되었습니다: {result.get('document_name')} ({result.get('count')}문제)",
                link=f"/pdf-agent/{document_id}/questions"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"PDF 문제 생성 처리 실패: {str(e)}", exc_info=True)
        
        # 오류 알림
        await send_notification(
            db=db,
            user_id=user_id,
            type="system",
            message=f"PDF 문제 생성 중 오류가 발생했습니다: {str(e)}",
            link=f"/pdf-agent/{document_id}"
        )
        
        # 작업 상태 업데이트
        task_manager.update_job_progress(job_id, 100, f"오류 발생: {str(e)}")
        
        return {"success": False, "error": str(e)}

async def process_pdf_answer(db: Session, document_id: int, question: str, user_id: int) -> Dict[str, Any]:
    """
    PDF 질문 답변 비동기 처리 핸들러
    
    Args:
        db: 데이터베이스 세션
        document_id: 문서 ID
        question: 질문 내용
        user_id: 사용자 ID
        
    Returns:
        처리 결과
    """
    job_id = f"answer_{document_id}_{user_id}"
    
    try:
        # 진행 상태 업데이트
        task_manager.update_job_progress(job_id, 10, "PDF 파싱 중...")
        
        # 답변 생성 (기본 구현)
        result = await PDFAgent.answer_question(db, document_id, question)
        
        # 진행 상태 업데이트
        task_manager.update_job_progress(job_id, 100, "답변 생성 완료")
        
        # 작업 완료 알림
        if result.get("success"):
            await send_notification(
                db=db,
                user_id=user_id,
                type="system",
                message=f"PDF 질문에 대한 답변이 준비되었습니다",
                link=f"/pdf-agent/{document_id}/qa"
            )
        
        return result
        
    except Exception as e:
        logger.error(f"PDF 답변 생성 처리 실패: {str(e)}", exc_info=True)
        
        # 오류 알림
        await send_notification(
            db=db,
            user_id=user_id,
            type="system",
            message=f"PDF 질문 답변 중 오류가 발생했습니다: {str(e)}",
            link=f"/pdf-agent/{document_id}"
        )
        
        # 작업 상태 업데이트
        task_manager.update_job_progress(job_id, 100, f"오류 발생: {str(e)}")
        
        return {"success": False, "error": str(e)}