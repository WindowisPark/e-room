import asyncio
import logging
from sqlalchemy.orm import Session

from app.services.pdf_agent.graphs.main import intergrate_graph
from app.services.pdf_agent.graphs.summary_graph import build_summary_graph
from app.services.pdf_agent.graphs.exam_graph import build_exam_graph
from app.services.pdf_agent.graphs.qa_graph import build_qa_graph
from app.services.pdf_agent.tools import get_initial_state
from app.services.notification_service import create_system_notification
from app.core.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)

class PDFAIService:
    """
    LangGraph 기반 PDF AI 서비스 클래스
    - 상태 기반 LangGraph 흐름 실행
    - 알림 전송 및 WebSocket 브로드캐스트 포함
    """

    def __init__(self):
        self.ws = WebSocketManager()

    async def run_document_processing(self, db: Session, user_id: str, folder: str) -> dict:
        """LangGraph 메인 흐름 실행 (전처리 등)"""
        try:
            graph = intergrate_graph()
            state = get_initial_state(user_id=user_id, folder=folder)
            result = await asyncio.to_thread(graph.invoke, state)
            return {
                "success": True,
                "result": result.get("result", "")
            }
        except Exception as e:
            logger.error(f"문서 처리 실패: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def run_summary(self, db: Session, user_id: str, folder: str, level: str = "default") -> dict:
        """요약 흐름 실행 + 알림 + WebSocket"""
        try:
            graph = build_summary_graph()
            state = get_initial_state(user_id=user_id, folder=folder)
            state["purpose"] = "summarize"
            state["summary_level"] = level
            result = await asyncio.to_thread(graph.invoke, state)
            summary_text = result.get("result", "")

            await create_system_notification(
                db=db,
                user_id=user_id,
                message=f"[{folder}] 문서 요약이 완료되었습니다.",
                link=f"/documents/{folder}/summary"
            )

            self.ws.send_to_user(user_id, {
                "type": "summary_complete",
                "folder": folder,
                "summary": summary_text
            })

            return {
                "success": True,
                "summary": summary_text
            }
        except Exception as e:
            logger.error(f"요약 실패: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def run_question_generation(self, db: Session, user_id: str, folder: str, count: int = 5) -> dict:
        """문제 생성 흐름 실행 + 알림 + WebSocket"""
        try:
            graph = build_exam_graph()
            state = get_initial_state(user_id=user_id, folder=folder)
            state["purpose"] = "generate_questions"
            state["question_count"] = count
            result = await asyncio.to_thread(graph.invoke, state)
            questions = result.get("result", "")

            await create_system_notification(
                db=db,
                user_id=user_id,
                message=f"[{folder}] 문제 생성이 완료되었습니다.",
                link=f"/documents/{folder}/exam"
            )

            self.ws.send_to_user(user_id, {
                "type": "exam_ready",
                "folder": folder,
                "question_count": count,
                "questions": questions
            })

            return {
                "success": True,
                "questions": questions
            }
        except Exception as e:
            logger.error(f"문제 생성 실패: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def run_qa(self, db: Session, user_id: str, folder: str, query: str) -> dict:
        """질의응답 흐름 실행 + 알림 + WebSocket"""
        try:
            graph = build_qa_graph()
            state = get_initial_state(user_id=user_id, folder=folder)
            state["purpose"] = "qa"
            state["query"] = query
            result = await asyncio.to_thread(graph.invoke, state)
            answer = result.get("result", "")

            await create_system_notification(
                db=db,
                user_id=user_id,
                message=f"[{folder}] 질문에 대한 답변이 도착했습니다.",
                link=f"/documents/{folder}/qa"
            )

            self.ws.send_to_user(user_id, {
                "type": "qa_answer",
                "folder": folder,
                "query": query,
                "answer": answer
            })

            return {
                "success": True,
                "answer": answer
            }
        except Exception as e:
            logger.error(f"질의응답 실패: {str(e)}", exc_info=True)
            return {"success": False, "error": str(e)}
