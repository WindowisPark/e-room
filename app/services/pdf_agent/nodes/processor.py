# app/services/pdf_agent/nodes/processor.py

from typing import Dict, Any, List
from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.chromadb_service import ChromaDBService
from app.models.tag import PDFFile
import asyncio
import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def load_pdf_text(state: AgentState) -> Dict[str, Any]:
    """
    PDF 텍스트 추출 노드 - 파일 경로에서 PDF 텍스트 로드
    
    Args:
        state: LangGraph 상태 객체
        
    Returns:
        업데이트된 상태 객체 (텍스트와 구조 정보 추가)
    """
    from app.db.session import SessionLocal
    
    try:
        # 데이터베이스 세션 생성
        db = SessionLocal()
        
        # 상태에서 문서 ID 가져오기
        document_id = state.get("document_id")
        logger.info(f"PDF 로드 시작: document_id={document_id}")
        
        if not document_id:
            logger.error(f"document_id가 상태에 없습니다: {state}")
            return {
                **state,
                "error": "document_id가 상태에 없습니다"
            }
            
        # PDF 파일 조회
        pdf_file = db.query(PDFFile).filter(PDFFile.id == document_id).first()
        if not pdf_file:
            raise ValueError(f"문서 ID {document_id}에 해당하는 PDF를 찾을 수 없습니다")
            
        # 파일 존재 확인
        file_path = pdf_file.file_path
        if not os.path.exists(file_path):
            raise ValueError(f"파일이 존재하지 않습니다: {file_path}")
            
        # PDF 파싱
        from app.services.pdf_agent.processor import PDFProcessor
        
        parsed_result = asyncio.run(PDFProcessor.parse_document(pdf_file))
        if not parsed_result.get("success"):
            error_msg = parsed_result.get("error", "PDF 파싱 실패")
            logger.error(f"PDF 파싱 실패: {error_msg}")
            return {
                **state,
                "error": error_msg
            }
        
        # 텍스트 확인 로깅 추가
        text = parsed_result.get("text", "")
        logger.info(f"PDF 텍스트 추출 결과: {len(text)} 글자")
        if not text:
            logger.warning("추출된 텍스트가 없습니다!")
            
        # 결과 반환 - 새 상태 딕셔너리 생성
        return {
            **state,
            "pdf_text": text,
            "pdf_metadata": parsed_result.get("metadata", {}),
            "structure": parsed_result.get("structure", {})
        }
        
    except Exception as e:
        logger.error(f"PDF 로드 중 오류: {str(e)}")
        return {
            **state,
            "error": f"PDF 로드 실패: {str(e)}"
        }
    finally:
        if 'db' in locals():
            db.close()

def split_into_chunks(state: AgentState) -> Dict[str, Any]:
    """
    PDF 텍스트를 청크로 분할
    
    Args:
        state: LangGraph 상태 객체 (pdf_text와 structure 포함)
        
    Returns:
        업데이트된 상태 객체 (청크 목록 추가)
    """
    try:
        # 텍스트와 구조 정보 가져오기
        text = state.get("pdf_text", "")
        structure = state.get("structure", {})
        
        if not text:
            raise ValueError("PDF 텍스트가 없습니다")
            
        # 청크 생성
        from app.services.pdf_agent.processor import PDFProcessor
        
        chunks = asyncio.run(PDFProcessor.chunk_document(text, structure))
        if not chunks:
            raise ValueError("텍스트 청킹 실패 또는 빈 텍스트")
            
        # 결과 반환
        return {
            **state,
            "doc_chunks": chunks  # 'pdfs' 대신 'doc_chunks'로 이름 변경하여 충돌 방지
        }
        
    except Exception as e:
        logger.error(f"청크 분할 중 오류: {str(e)}")
        return {
            **state,
            "error": f"청크 분할 실패: {str(e)}"
        }

def store_embedding(state: AgentState) -> Dict[str, Any]:
    """
    청크를 ChromaDB에 저장
    
    Args:
        state: LangGraph 상태 객체 (doc_chunks 포함)
        
    Returns:
        업데이트된 상태 객체
    """
    try:
        # 필요한 상태 값 가져오기
        user_id = int(state.get("user_id", 0))
        folder = state.get("folder", "default")
        document_id = int(state.get("document_id", 0))
        chunks = state.get("doc_chunks", [])
        
        if not chunks:
            raise ValueError("저장할 청크가 없습니다")
            
        if not user_id or not document_id:
            raise ValueError("사용자 ID 또는 문서 ID가 유효하지 않습니다")
            
        # ChromaDB에 저장
        chroma_service = ChromaDBService()
        success = chroma_service.add_document_chunks(user_id, document_id, folder, chunks)
        
        if not success:
            raise ValueError("ChromaDB 저장 실패")
            
        # 성공 메시지 추가
        return {
            **state,
            "embedding_stored": True,
            "embedding_message": f"문서 ID {document_id}의 {len(chunks)}개 청크가 ChromaDB에 저장되었습니다."
        }
        
    except Exception as e:
        logger.error(f"임베딩 저장 중 오류: {str(e)}")
        return {
            **state,
            "embedding_stored": False,
            "error": f"임베딩 저장 실패: {str(e)}"
        }