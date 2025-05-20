# app/services/pdf_agent/nodes/processor.py

from typing import Dict, Any, List
from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.chromadb_service import ChromaDBService
from app.models.tag import PDFFile
from app.services.pdf_agent.processor import PDFProcessor
import asyncio
import nest_asyncio
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
        # 상태 객체 로깅
        logger.info(f"PDF 로드 함수 호출됨, 상태 객체 키: {list(state.keys() if isinstance(state, dict) else [])}")
        
        # 데이터베이스 세션 생성
        db = SessionLocal()
        
        # 상태에서 문서 ID와 파일 경로 가져오기
        document_id = state.get("document_id") if isinstance(state, dict) else None
        pdf_path = state.get("pdf_path") if isinstance(state, dict) else None
        
        logger.info(f"PDF 로드 시작: document_id={document_id}, pdf_path={pdf_path}")
        
        # 파일 경로가 직접 제공된 경우 사용
        if pdf_path and os.path.exists(pdf_path):
            logger.info(f"제공된 파일 경로 사용: {pdf_path}")
            
            # 결과 반환 - 새 상태 딕셔너리 생성 (임시)
            return {
                **state,
                "pdf_text": "임시 텍스트",  # 일단 더미 텍스트로 진행
                "pdf_metadata": {"dummy": "data"},
                "structure": {"sections": []}
            }
        
        # 파일 경로가 없을 경우 DB에서 조회
        elif document_id:
            logger.info(f"DB에서 파일 정보 조회: document_id={document_id}")
            # PDF 파일 조회
            pdf_file = db.query(PDFFile).filter(PDFFile.id == document_id).first()
            if not pdf_file:
                raise ValueError(f"문서 ID {document_id}에 해당하는 PDF를 찾을 수 없습니다")
                
            # PDF 파싱
            from app.services.pdf_agent.processor import PDFProcessor
            
            try:
                nest_asyncio.apply()
                loop = asyncio.get_event_loop()
                parsed_result = loop.run_until_complete(PDFProcessor.parse_document(pdf_file))
            except ImportError:
                # nest_asyncio가 설치되지 않은 경우
                # 간단한 대안으로 동기식 처리
                logger.warning("nest_asyncio가 설치되지 않아 동기식으로 처리합니다.")
                parsed_result = {
                    "success": True, 
                    "text": "임시 텍스트", 
                    "metadata": {"dummy": "data"}, 
                    "structure": {"sections": []}
                }
            if not parsed_result.get("success"):
                raise ValueError(parsed_result.get("error", "PDF 파싱 실패"))
                
            # 결과 반환 - 새 상태 딕셔너리 생성
            return {
                **state,
                "pdf_text": parsed_result.get("text", ""),
                "pdf_metadata": parsed_result.get("metadata", {}),
                "structure": parsed_result.get("structure", {})
            }
        else:
            raise ValueError("PDF 문서 ID 또는 파일 경로가 필요합니다")
            
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
        
        logger.info(f"청크 분할 시작: 텍스트 길이 {len(text)}, 구조 정보 존재: {'sections' in structure}")
        
        if not text:
            logger.error("PDF 텍스트가 없습니다")
            return {
                **state,
                "error": "PDF 텍스트가 없습니다",
                "doc_chunks": []  # 빈 청크 목록 명시적 설정
            }
            
        # 청크 생성 - asyncio.run() 대신 동기식 버전의 함수 사용
        from app.services.pdf_agent.processor import PDFProcessor
        
        # 비동기 함수를 호출하지 않고 동기식 버전 사용
        chunks = PDFProcessor._chunk_by_paragraphs(text, 1000, 200)  # 임시로 하드코딩된 값 사용
        
        if not chunks:
            logger.warning("텍스트 청킹 결과가 비어있습니다")
            
        logger.info(f"청크 분할 완료: {len(chunks)}개 청크 생성")
            
        # 결과 반환
        return {
            **state,
            "doc_chunks": chunks
        }
        
    except Exception as e:
        logger.error(f"청크 분할 중 오류: {str(e)}", exc_info=True)
        return {
            **state,
            "error": f"청크 분할 실패: {str(e)}",
            "doc_chunks": []  # 빈 청크 목록 명시적 설정
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
        user_id = state.get("user_id", "0")
        folder = state.get("folder", "default")
        document_id = state.get("document_id", 0)
        chunks = state.get("doc_chunks", [])
        
        logger.info(f"임베딩 저장 시작: user_id={user_id}, doc_id={document_id}, 청크 수={len(chunks)}")
        
        # 값 검증
        if not chunks:
            logger.error("저장할 청크가 없습니다")
            return {
                **state,
                "embedding_stored": False,
                "error": "저장할 청크가 없습니다"
            }
            
        if not user_id or not document_id:
            logger.error(f"사용자 ID 또는 문서 ID가 유효하지 않습니다: user_id={user_id}, doc_id={document_id}")
            return {
                **state,
                "embedding_stored": False,
                "error": "사용자 ID 또는 문서 ID가 유효하지 않습니다"
            }
            
        # user_id가 문자열인 경우 정수로 변환
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            logger.error(f"user_id를 정수로 변환할 수 없습니다: {user_id}")
            return {
                **state,
                "embedding_stored": False,
                "error": f"user_id 형식 오류: {user_id}"
            }
            
        # 정수 변환 확인
        if isinstance(document_id, str):
            try:
                document_id = int(document_id)
            except (ValueError, TypeError):
                logger.error(f"document_id를 정수로 변환할 수 없습니다: {document_id}")
                return {
                    **state,
                    "embedding_stored": False,
                    "error": f"document_id 형식 오류: {document_id}"
                }
        
        # ChromaDB에 저장
        chroma_service = ChromaDBService()
        success = chroma_service.add_document_chunks(user_id_int, document_id, folder, chunks)
        
        if not success:
            logger.error("ChromaDB 저장 실패")
            return {
                **state,
                "embedding_stored": False,
                "error": "ChromaDB 저장 실패"
            }
            
        # 성공 메시지 추가
        logger.info(f"문서 ID {document_id}의 {len(chunks)}개 청크가 ChromaDB에 저장되었습니다")
        return {
            **state,
            "embedding_stored": True,
            "embedding_message": f"문서 ID {document_id}의 {len(chunks)}개 청크가 ChromaDB에 저장되었습니다"
        }
        
    except Exception as e:
        logger.error(f"임베딩 저장 중 오류: {str(e)}", exc_info=True)
        return {
            **state,
            "embedding_stored": False,
            "error": f"임베딩 저장 실패: {str(e)}"
        }