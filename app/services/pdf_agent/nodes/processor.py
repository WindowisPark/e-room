# app/services/pdf_agent/nodes/processor.py

from typing import Dict, Any
from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.processor import PDFProcessor
from app.services.pdf_agent.chromadb_service import ChromaDBService
import logging
import os

logger = logging.getLogger(__name__)

def load_pdf_text(state: AgentState) -> Dict[str, Any]:
    pdf_path = state.get("pdf_path")
    if not pdf_path or not os.path.exists(pdf_path):
        logger.error(f"PDF 경로가 유효하지 않음: {pdf_path}")
        return {**state, "error": f"유효하지 않은 파일 경로: {pdf_path}"}

    logger.info(f"gptpdf로 PDF 파싱 시작: {pdf_path}")
    try:
        result = PDFProcessor.parse_and_split(pdf_path)
        return {
            **state,
            "pdf_text": result["text"],
            "images": result["images"],
            "doc_chunks": result["chunks"]
        }
    except Exception as e:
        logger.error(f"gptpdf 파싱 실패: {str(e)}", exc_info=True)
        return {**state, "error": f"PDF 파싱 실패: {str(e)}"}

def store_embedding(state: AgentState) -> Dict[str, Any]:
    user_id = int(state.get("user_id", 0))
    document_id = int(state.get("document_id", 0))
    folder = state.get("folder", "default")
    chunks = state.get("doc_chunks", [])

    logger.info(f"ChromaDB 저장 시작: user_id={user_id}, doc_id={document_id}, chunks={len(chunks)}")
    if not chunks:
        return {**state, "embedding_stored": False, "error": "청크가 없습니다."}

    success = PDFProcessor.store_chunks(user_id, document_id, folder, chunks)
    return {
        **state,
        "embedding_stored": success,
        "error": None if success else "ChromaDB 저장 실패"
    }
