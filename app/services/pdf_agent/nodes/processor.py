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
            
            try:
                # PyMuPDF 또는 다른 라이브러리로 직접 PDF 텍스트 추출
                try:
                    import fitz  # PyMuPDF
                    
                    logger.info(f"PyMuPDF로 파일 열기: {pdf_path}")
                    doc = fitz.open(pdf_path)
                    pdf_text = ""
                    metadata = {"page_count": len(doc)}
                    structure = {"sections": []}
                    
                    for i, page in enumerate(doc):
                        text = page.get_text()
                        pdf_text += text + "\n\n"
                        
                        # 기본적인 구조 정보 추출 시도
                        lines = text.split("\n")
                        for j, line in enumerate(lines):
                            if line.strip() and (line.isupper() or "CHAPTER" in line or "Section" in line):
                                structure["sections"].append({
                                    "title": line.strip(),
                                    "page": i + 1,
                                    "index": len(structure["sections"]),
                                    "start_char": len(pdf_text) - len(text) + text.find(line)
                                })
                                
                    logger.info(f"PyMuPDF로 텍스트 추출 성공: {len(pdf_text)} 문자")
                    
                except ImportError:
                    logger.warning("PyMuPDF를 가져올 수 없습니다. 대체 방법으로 pdfplumber 시도")
                    
                    # PDFPlumber로 시도
                    try:
                        import pdfplumber
                        
                        logger.info(f"pdfplumber로 파일 열기: {pdf_path}")
                        with pdfplumber.open(pdf_path) as pdf:
                            pdf_text = ""
                            metadata = {"page_count": len(pdf.pages)}
                            structure = {"sections": []}
                            
                            for i, page in enumerate(pdf.pages):
                                text = page.extract_text() or ""
                                pdf_text += text + "\n\n"
                                
                            logger.info(f"pdfplumber로 텍스트 추출 성공: {len(pdf_text)} 문자")
                            
                    except ImportError:
                        logger.error("PDF 처리에 필요한 라이브러리가 없습니다. PyMuPDF 또는 pdfplumber를 설치하세요.")
                        pdf_text = "PDF 텍스트 추출 실패: 필요한 라이브러리가 없습니다."
                        metadata = {}
                        structure = {"sections": []}
                
                # 텍스트가 비어있는지 확인
                if not pdf_text.strip():
                    logger.warning(f"추출된 텍스트가 비어있습니다. PDF 파일이 보호되어 있거나 텍스트 추출이 불가능할 수 있습니다.")
                    # 더미 텍스트 생성 (디버깅용)
                    pdf_text = f"이 텍스트는 {pdf_path} 파일에서 추출에 실패한 경우 생성된 더미 텍스트입니다."
                
                logger.info(f"PDF 텍스트 추출 완료: {len(pdf_text)} 문자")
                
                # 결과 반환
                return {
                    **state,
                    "pdf_text": pdf_text,
                    "pdf_metadata": metadata,
                    "structure": structure
                }
                
            except Exception as e:
                logger.error(f"PDF 텍스트 추출 실패: {str(e)}", exc_info=True)
                # 더미 텍스트로 계속 진행
                return {
                    **state,
                    "error": f"PDF 텍스트 추출 실패: {str(e)}",
                    "pdf_text": f"이 텍스트는 {pdf_path} 파일에서 추출에 실패한 경우 생성된 더미 텍스트입니다. 오류: {str(e)}"
                }
            
        # 파일 경로가 없을 경우 DB에서 조회
        elif document_id:
            logger.info(f"DB에서 파일 정보 조회: document_id={document_id}")
            # PDF 파일 조회
            pdf_file = db.query(PDFFile).filter(PDFFile.id == document_id).first()
            if not pdf_file:
                raise ValueError(f"문서 ID {document_id}에 해당하는 PDF를 찾을 수 없습니다")
            
            # PDF 파일 경로 가져오기
            file_path = pdf_file.file_path
            logger.info(f"DB에서 파일 경로 조회: {file_path}")
            
            # 파일이 존재하는지 확인
            if not os.path.exists(file_path):
                logger.error(f"파일이 존재하지 않습니다: {file_path}")
                # 더미 텍스트로 계속 진행
                return {
                    **state,
                    "error": f"파일이 존재하지 않습니다: {file_path}",
                    "pdf_text": f"이 텍스트는 {file_path} 파일이 존재하지 않아 생성된 더미 텍스트입니다."
                }
            
            # 직접 PDF 텍스트 추출 (비동기 호출 없이)
            try:
                # PyMuPDF 사용
                try:
                    import fitz  # PyMuPDF
                    
                    logger.info(f"PyMuPDF로 파일 열기: {file_path}")
                    doc = fitz.open(file_path)
                    pdf_text = ""
                    metadata = {"page_count": len(doc)}
                    structure = {"sections": []}
                    
                    for i, page in enumerate(doc):
                        text = page.get_text()
                        pdf_text += text + "\n\n"
                        
                    logger.info(f"PyMuPDF로 텍스트 추출 성공: {len(pdf_text)} 문자")
                    
                except ImportError:
                    logger.warning("PyMuPDF를 가져올 수 없습니다. 대체 방법으로 pdfplumber 시도")
                    
                    # PDFPlumber로 시도
                    try:
                        import pdfplumber
                        
                        logger.info(f"pdfplumber로 파일 열기: {file_path}")
                        with pdfplumber.open(file_path) as pdf:
                            pdf_text = ""
                            metadata = {"page_count": len(pdf.pages)}
                            structure = {"sections": []}
                            
                            for i, page in enumerate(pdf.pages):
                                text = page.extract_text() or ""
                                pdf_text += text + "\n\n"
                                
                            logger.info(f"pdfplumber로 텍스트 추출 성공: {len(pdf_text)} 문자")
                            
                    except ImportError:
                        logger.error("PDF 처리에 필요한 라이브러리가 없습니다. PyMuPDF 또는 pdfplumber를 설치하세요.")
                        pdf_text = "PDF 텍스트 추출 실패: 필요한 라이브러리가 없습니다."
                        metadata = {}
                        structure = {"sections": []}
                
                # 텍스트가 비어있는지 확인
                if not pdf_text.strip():
                    logger.warning(f"추출된 텍스트가 비어있습니다. PDF 파일이 보호되어 있거나 텍스트 추출이 불가능할 수 있습니다.")
                    # 더미 텍스트 생성 (디버깅용)
                    pdf_text = f"이 텍스트는 {file_path} 파일에서 추출에 실패한 경우 생성된 더미 텍스트입니다."
                
                logger.info(f"PDF 텍스트 추출 완료: {len(pdf_text)} 문자, 저장 경로: {file_path}")
                
                # 결과 반환
                return {
                    **state,
                    "pdf_text": pdf_text,
                    "pdf_metadata": metadata,
                    "structure": structure
                }
                
            except Exception as e:
                logger.error(f"PDF 텍스트 추출 실패: {str(e)}", exc_info=True)
                # 더미 텍스트로 계속 진행
                return {
                    **state,
                    "error": f"PDF 텍스트 추출 실패: {str(e)}",
                    "pdf_text": f"이 텍스트는 {file_path} 파일에서 추출에 실패한 경우 생성된 더미 텍스트입니다. 오류: {str(e)}"
                }
        else:
            error_msg = "PDF 문서 ID 또는 파일 경로가 필요합니다"
            logger.error(error_msg)
            return {
                **state,
                "error": error_msg,
                "pdf_text": ""
            }
            
    except Exception as e:
        logger.error(f"PDF 로드 중 오류: {str(e)}", exc_info=True)
        return {
            **state,
            "error": f"PDF 로드 실패: {str(e)}",
            "pdf_text": f"이 텍스트는 PDF 로드 중 오류로 인해 생성된 더미 텍스트입니다. 오류: {str(e)}"
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
        
        # 로깅 추가
        if text:
            logger.info(f"텍스트 샘플 (처음 200자): {text[:200]}")
        
        if not text:
            logger.error("PDF 텍스트가 없습니다. load_pdf_text 함수가 제대로 동작했는지 확인하세요.")
            return {
                **state,
                "error": "PDF 텍스트가 없습니다",
                "doc_chunks": []  # 빈 청크 목록 명시적 설정
            }
            
        # 청크 생성 - PDFProcessor 모듈 사용하여 텍스트 분할
        try:
            # 긴 텍스트를 청크로 분할
            from app.services.pdf_agent.processor import PDFProcessor
            
            # 청크 크기와 오버랩은 설정 파일에서 가져오거나 기본값 사용
            from app.core.config import settings
            
            chunk_size = settings.PDF_CHUNK_SIZE if hasattr(settings, 'PDF_CHUNK_SIZE') else 1000
            chunk_overlap = settings.PDF_CHUNK_OVERLAP if hasattr(settings, 'PDF_CHUNK_OVERLAP') else 200
            
            logger.info(f"텍스트 분할 시작: 청크 크기={chunk_size}, 오버랩={chunk_overlap}")
            
            if hasattr(PDFProcessor, '_chunk_by_paragraphs'):
                chunks = PDFProcessor._chunk_by_paragraphs(text, chunk_size, chunk_overlap)
                logger.info(f"_chunk_by_paragraphs 메소드로 {len(chunks)}개 청크 생성됨")
            else:
                # 메소드가 없으면 대체 로직 
                chunks = []
                paragraphs = text.split('\n\n')
                for i, para in enumerate(paragraphs):
                    if para.strip():
                        chunks.append({
                            "index": i,
                            "text": para.strip(),
                            "start_char": text.find(para),
                            "end_char": text.find(para) + len(para)
                        })
                logger.info(f"대체 방식으로 {len(chunks)}개 청크 생성됨")
        except AttributeError as e:
            logger.error(f"PDFProcessor 메소드 호출 실패: {str(e)}")
            chunks = []
        except Exception as e:
            logger.error(f"청크 생성 중 예외 발생: {str(e)}")
            chunks = []
        
        if not chunks:
            logger.warning("텍스트 청킹 결과가 비어있습니다. 텍스트 형식이나 분할 로직을 확인하세요.")
        else:
            logger.info(f"청크 분할 완료: {len(chunks)}개 청크 생성")
            # 첫 번째 청크 샘플 로깅
            if chunks:
                sample_chunk = chunks[0]
                logger.info(f"첫 번째 청크 샘플: index={sample_chunk.get('index')}, 텍스트 길이={len(sample_chunk.get('text', ''))}")
            
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
        result = {
            **state,
            "embedding_stored": True,
            "embedding_message": f"문서 ID {document_id}의 {len(chunks)}개 청크가 ChromaDB에 저장되었습니다"
        }

        # 확인용 로깅 추가
        logger.info(f"반환되는 상태 객체: embedding_stored={result.get('embedding_stored')}, doc_chunks 길이={len(result.get('doc_chunks', []))}")
        
        return result
        
    except Exception as e:
        logger.error(f"임베딩 저장 중 오류: {str(e)}", exc_info=True)
        return {
            **state,
            "embedding_stored": False,
            "error": f"임베딩 저장 실패: {str(e)}"
        }