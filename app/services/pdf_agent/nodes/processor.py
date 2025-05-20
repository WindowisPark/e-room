# app/services/pdf_agent/nodes/processor.py

from app.services.pdf_agent.processor import PDFProcessor
from app.services.pdf_agent.states import AgentState
from app.models.tag import PDFFile
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.services.pdf_agent.chromadb_service import ChromaDBService
import asyncio

def load_pdf_text(state: AgentState) -> AgentState:
    """
    PDF 텍스트 추출 노드 - processor.py의 parse_document 사용
    """
    from app.db.session import SessionLocal
    db: Session = SessionLocal()

    document_id = int(state["document_id"])
    pdf_obj: PDFFile = db.query(PDFFile).filter(PDFFile.id == document_id).first()

    if not pdf_obj:
        raise ValueError(f"PDFFile {document_id} 를 찾을 수 없습니다")

    parsed_result = asyncio.run(PDFProcessor.parse_document(pdf_obj))
    if not parsed_result.get("success"):
        raise ValueError(parsed_result.get("error", "PDF 파싱 실패"))

    return {
        **state,
        "pdf_text": parsed_result["text"],
        "structure": parsed_result["structure"]
    }

def split_into_chunks(state: AgentState) -> AgentState:
    """
    LangGraph용 청크 분할 노드 (기존 PDFProcessor 기반)
    """
    text = state.get("pdf_text", "")
    structure = state.get("structure", {})

    chunks = asyncio.run(PDFProcessor.chunk_document(text, structure))
    if not chunks:
        raise ValueError("텍스트 청크 분리 실패 또는 빈 텍스트")

    return {**state, "chunks": chunks}

def store_embedding(state: AgentState) -> AgentState:
    user_id = int(state["user_id"])
    folder = state["folder"]
    document_id = int(state["document_id"])
    chunks = state.get("chunks", [])

    if not chunks:
        raise ValueError("청크가 없습니다")

    success = ChromaDBService().add_document_chunks(user_id, document_id, folder, chunks)
    if not success:
        raise ValueError("ChromaDB 저장 실패")

    return state