from typing import Dict, List, Any, Optional, Tuple
import os
import tempfile
import logging
import re
import json
import shutil
import numpy as np
from pathlib import Path
from datetime import datetime
import pdfplumber
from pdf2image import convert_from_path
import pytesseract
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.core.config import settings
from app.models.tag import PDFFile
from app.services.file_service import FileStorageManager
from app.crud.crud_tag import get_pdf_by_id
from app.services.pdf_agent.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)

class PDFProcessor:
    """
    PDF 문서 처리 및 분석 담당 클래스
    - 문서 파싱, 청킹, 임베딩 생성 등 처리
    """
    
    @staticmethod
    async def parse_document(db_pdf: PDFFile) -> Dict[str, Any]:
        """
        PDF 문서 파싱 및 텍스트 추출
        
        Args:
            db_pdf: PDF 파일 DB 모델
            
        Returns:
            파싱 결과 (텍스트, 메타데이터 등)
        """
        try:
            # 파일 경로 확인
            file_path = db_pdf.file_path
            if not os.path.exists(file_path):
                return {"error": "파일을 찾을 수 없습니다", "success": False}
            
            # 임시 작업 디렉토리 생성
            with tempfile.TemporaryDirectory() as temp_dir:
                # 최적화된 복사본 생성 (필요한 경우)
                optimized_path = os.path.join(temp_dir, "optimized.pdf")
                try:
                    PDFProcessor._optimize_pdf(file_path, optimized_path)
                    working_path = optimized_path
                except Exception as e:
                    logger.warning(f"PDF 최적화 실패, 원본 사용: {str(e)}")
                    working_path = file_path
                
                # PDF 텍스트 추출
                extracted_text, is_scanned = PDFProcessor._extract_text_with_fallback(working_path)
                
                # 메타데이터 추출
                metadata = PDFProcessor._extract_metadata(working_path)
                metadata["is_scanned"] = is_scanned
                
                # 구조 정보 추출 (목차, 헤더 등)
                structure_info = PDFProcessor._extract_structure(working_path)
                
                # 결과 반환
                return {
                    "success": True,
                    "document_id": db_pdf.id,
                    "filename": db_pdf.filename,
                    "text": extracted_text,
                    "metadata": metadata,
                    "structure": structure_info,
                    "page_count": metadata.get("page_count", 0),
                    "processed_at": datetime.utcnow().isoformat()
                }
        
        except Exception as e:
            logger.error(f"PDF 파싱 실패: {str(e)}", exc_info=True)
            return {"error": f"PDF 파싱 중 오류 발생: {str(e)}", "success": False}
    
    @staticmethod
    async def chunk_document(
        text: str, 
        structure: Optional[Dict[str, Any]] = None,
        chunk_size: int = None, 
        overlap: int = None
    ) -> List[Dict[str, Any]]:
        """
        문서를 의미 단위로 청킹
        
        Args:
            text: 추출된 문서 텍스트
            structure: 문서 구조 정보 (목차, 헤더 등)
            chunk_size: 청크 크기 (문자 수)
            overlap: 청크 간 중복 문자 수
            
        Returns:
            청크 목록
        """
        # 설정값 로드 (없으면 기본값 사용)
        chunk_size = chunk_size or settings.PDF_CHUNK_SIZE
        overlap = overlap or settings.PDF_CHUNK_OVERLAP
        
        # 텍스트가 없으면 빈 리스트 반환
        if not text or len(text.strip()) == 0:
            return []
        
        chunks = []
        
        # 1. 구조 정보가 있으면 섹션 기반 청킹
        if structure and structure.get("sections"):
            return PDFProcessor._chunk_by_sections(text, structure["sections"], chunk_size, overlap)
        
        # 2. 구조 정보가 없으면 문단 기반 청킹
        return PDFProcessor._chunk_by_paragraphs(text, chunk_size, overlap)
    
    @staticmethod
    async def create_embeddings(db: Session, chunks: List[Dict[str, Any]], document_id: int) -> List[Dict[str, Any]]:
        """청크별 임베딩 생성 및 저장"""
        if not chunks:
            return []
            
        try:
            # OpenAI API 또는 다른 임베딩 모델을 사용하여 임베딩 생성
            from openai import OpenAI
            
            client = OpenAI(api_key=settings.AI_API_KEY)
            embedded_chunks = []
            
            # 청크를 배치로 처리 (API 호출 최소화)
            batch_size = 10  # API 한계를 고려하여 조정
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]
                batch_texts = [chunk["text"] for chunk in batch]
                
                # 임베딩 생성 요청
                response = client.embeddings.create(
                    input=batch_texts,
                    model=settings.AI_EMBEDDING_MODEL
                )
                
                # 각 청크에 임베딩 추가
                for j, chunk in enumerate(batch):
                    embedding_vector = response.data[j].embedding
                    
                    # pgvector 사용하여 DB에 저장
                    # 직접 SQL 쿼리 실행 (SQLAlchemy ORM 모델이 없는 경우)
                    query = text("""
                        INSERT INTO document_chunks 
                        (document_id, chunk_index, text, start_char, end_char, embedding) 
                        VALUES (:document_id, :chunk_index, :text, :start_char, :end_char, :embedding::vector)
                    """)
                    
                    db.execute(query, {
                        "document_id": document_id,
                        "chunk_index": chunk["index"],
                        "text": chunk["text"],
                        "start_char": chunk["start_char"],
                        "end_char": chunk["end_char"],
                        "embedding": json.dumps(embedding_vector)  # PostgreSQL이 vector 타입으로 변환
                    })
                    
                    embedded_chunks.append({
                        **chunk,
                        "embedding": embedding_vector
                    })
                        
                db.commit()
                return embedded_chunks
                
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {str(e)}", exc_info=True)
            db.rollback()
            
            # 임베딩 생성 실패해도 청크는 반환
            return chunks
    
    @staticmethod
    def search_similar_chunks(db: Session, query: str, document_id: int, limit: int = 3) -> List[Dict[str, Any]]:
        """쿼리와 유사한 청크 검색"""
        try:
            # 쿼리 임베딩 생성
            from openai import OpenAI
            
            client = OpenAI(api_key=settings.AI_API_KEY)
            query_response = client.embeddings.create(
                input=query,
                model=settings.AI_EMBEDDING_MODEL
            )
            query_embedding = query_response.data[0].embedding
            
            # pgvector의 연산자를 사용하여 유사한 청크 검색
            query = text("""
                SELECT document_id, chunk_index, text, start_char, end_char
                FROM document_chunks
                WHERE document_id = :document_id
                ORDER BY embedding <=> :query_embedding::vector
                LIMIT :limit
            """)
            
            similar_chunks = db.execute(query, {
                "document_id": document_id,
                "query_embedding": json.dumps(query_embedding),
                "limit": limit
            }).fetchall()
            
            # 결과 형식화
            result = []
            for chunk in similar_chunks:
                result.append({
                    "document_id": chunk.document_id,
                    "index": chunk.chunk_index,
                    "text": chunk.text,
                    "start_char": chunk.start_char,
                    "end_char": chunk.end_char,
                })
            
            return result
            
        except Exception as e:
            logger.error(f"유사 청크 검색 실패: {str(e)}", exc_info=True)
            return []
    
    # 내부 메서드 (Private Methods)
    
    @staticmethod
    def _optimize_pdf(input_path: str, output_path: str) -> bool:
        """
        PDF 파일 최적화 (용량 감소, 처리 준비)
        
        Args:
            input_path: 입력 PDF 경로
            output_path: 출력 PDF 경로
            
        Returns:
            성공 여부
        """
        try:
            # 실제 구현에서는 ghostscript 또는 다른 도구 사용
            # 예시: gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook -dNOPAUSE -dQUIET -dBATCH -sOutputFile=output.pdf input.pdf
            
            # 임시 구현: 단순 복사
            shutil.copy(input_path, output_path)
            
            return True
        except Exception as e:
            logger.error(f"PDF 최적화 실패: {str(e)}")
            # 최적화 실패 시 원본 파일 사용하도록 false 반환
            return False
    
    @staticmethod
    def _extract_text_with_fallback(file_path: str) -> Tuple[str, bool]:
        """
        PDF에서 텍스트 추출 (OCR 폴백 포함)
        
        Args:
            file_path: PDF 파일 경로
            
        Returns:
            (추출된 텍스트, 스캔된 문서 여부) 튜플
        """
        try:
            # 1. pdfplumber로 텍스트 추출 시도
            with pdfplumber.open(file_path) as pdf:
                all_text = ""
                is_scanned = True  # 초기값 설정
                
                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    all_text += page_text + "\n\n"  # 페이지 구분
                    
                    # 페이지에 텍스트가 있으면 스캔된 문서가 아닐 수 있음
                    if page_text.strip():
                        is_scanned = False
                
                # 텍스트가 충분히 있으면 OCR 필요 없음
                if len(all_text.strip()) > 100 or not is_scanned:
                    return all_text, False
                
            # 2. 텍스트가 거의 없으면 OCR 시도
            text_from_ocr = ""
            is_scanned = True
            
            # PDF를 이미지로 변환
            images = convert_from_path(file_path, dpi=300)
            
            for i, image in enumerate(images):
                # OCR 수행
                page_text = pytesseract.image_to_string(image, lang='kor+eng')
                text_from_ocr += page_text + "\n\n"
            
            return text_from_ocr, is_scanned
                
        except Exception as e:
            logger.error(f"텍스트 추출 실패: {str(e)}")
            return "", True  # 오류 발생 시 빈 문자열 반환
    
    @staticmethod
    def _extract_metadata(file_path: str) -> Dict[str, Any]:
        """
        PDF 메타데이터 추출
        
        Args:
            file_path: PDF 파일 경로
            
        Returns:
            메타데이터 딕셔너리
        """
        try:
            with pdfplumber.open(file_path) as pdf:
                # 파일 크기
                file_size = os.path.getsize(file_path)
                
                # 페이지 수
                page_count = len(pdf.pages)
                
                # PDF 메타데이터
                pdf_meta = pdf.metadata or {}
                
                # 메타데이터 형식화
                return {
                    "file_size": file_size,
                    "page_count": page_count,
                    "title": pdf_meta.get("Title", ""),
                    "author": pdf_meta.get("Author", ""),
                    "created_date": pdf_meta.get("CreationDate", ""),
                    "modified_date": pdf_meta.get("ModDate", ""),
                    "file_created_at": datetime.fromtimestamp(os.path.getctime(file_path)).isoformat(),
                    "file_modified_at": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat(),
                }
        except Exception as e:
            logger.error(f"메타데이터 추출 실패: {str(e)}")
            return {
                "file_size": os.path.getsize(file_path) if os.path.exists(file_path) else 0,
                "page_count": 0,
                "error": str(e)
            }
    
    @staticmethod
    def _extract_structure(file_path: str) -> Dict[str, Any]:
        """
        PDF 구조 정보 추출 (목차, 섹션 등)
        
        Args:
            file_path: PDF 파일 경로
            
        Returns:
            구조 정보 딕셔너리
        """
        try:
            structure = {"sections": []}
            
            with pdfplumber.open(file_path) as pdf:
                # 페이지별 텍스트 수집
                all_pages_text = []
                
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    all_pages_text.append(page_text)
                    
                    # 헤더 후보 찾기 (대문자로 시작하는 짧은 줄)
                    lines = page_text.split("\n")
                    for line_index, line in enumerate(lines):
                        line = line.strip()
                        
                        # 헤더 패턴 (간단한 휴리스틱)
                        if (line and len(line) < 100 and 
                            (line.isupper() or 
                             re.match(r"^(?:CHAPTER|Chapter|Section|\d+\.|\d+\s|\*|\[\d+\])\s", line))):
                            
                            # 섹션 정보 저장
                            structure["sections"].append({
                                "title": line,
                                "page": i + 1,
                                "index": len(structure["sections"]),
                                "start_char": sum(len(t) for t in all_pages_text[:i]) + 
                                              sum(len(l) for l in lines[:line_index]),
                            })
            
            return structure
                
        except Exception as e:
            logger.error(f"구조 정보 추출 실패: {str(e)}")
            return {"sections": [], "error": str(e)}
    
    @staticmethod
    def _chunk_by_sections(
        text: str, 
        sections: List[Dict[str, Any]], 
        chunk_size: int, 
        overlap: int
    ) -> List[Dict[str, Any]]:
        """
        섹션 기반 청킹
        
        Args:
            text: 전체 텍스트
            sections: 섹션 정보 목록
            chunk_size: 최대 청크 크기
            overlap: 오버랩 크기
            
        Returns:
            청크 목록
        """
        chunks = []
        
        # 섹션별 시작 위치 정렬
        sorted_sections = sorted(sections, key=lambda x: x.get("start_char", 0))
        
        # 청킹 처리
        for i, section in enumerate(sorted_sections):
            # 섹션 시작 위치
            start_pos = section.get("start_char", 0)
            
            # 섹션 종료 위치 (다음 섹션 시작 또는 텍스트 끝)
            end_pos = sorted_sections[i+1].get("start_char", len(text)) if i < len(sorted_sections) - 1 else len(text)
            
            # 섹션 내용
            section_text = text[start_pos:end_pos]
            section_title = section.get("title", "")
            
            # 섹션이 청크 크기보다 작으면 그대로 사용
            if len(section_text) <= chunk_size:
                chunks.append({
                    "index": len(chunks),
                    "text": section_title + "\n" + section_text,
                    "start_char": start_pos,
                    "end_char": end_pos,
                    "section": section_title,
                    "page": section.get("page", 1)
                })
            else:
                # 섹션이 크면 하위 청킹
                sub_chunks = PDFProcessor._chunk_text(section_text, chunk_size, overlap)
                
                for j, sub_chunk in enumerate(sub_chunks):
                    # 첫 청크에만 섹션 제목 추가
                    prefix = section_title + "\n" if j == 0 else ""
                    
                    # 청크 정보 저장
                    chunks.append({
                        "index": len(chunks),
                        "text": prefix + sub_chunk["text"],
                        "start_char": start_pos + sub_chunk["start_char"],
                        "end_char": start_pos + sub_chunk["end_char"],
                        "section": section_title,
                        "page": section.get("page", 1)
                    })
        
        return chunks
    
    @staticmethod
    def _chunk_by_paragraphs(text: str, chunk_size: int, overlap: int) -> List[Dict[str, Any]]:
        """
        문단 기반 청킹
        
        Args:
            text: 전체 텍스트
            chunk_size: 최대 청크 크기
            overlap: 오버랩 크기
            
        Returns:
            청크 목록
        """
        # 문단 구분 (빈 줄 기준)
        paragraphs = re.split(r"\n\s*\n", text)
        chunks = []
        
        current_chunk = ""
        current_start = 0
        last_end = 0
        
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
                
            # 문단 위치 계산
            para_start = text.find(para, last_end)
            para_end = para_start + len(para)
            last_end = para_end
            
            # 현재 청크에 문단 추가 가능한지 확인
            if len(current_chunk) + len(para) + 2 <= chunk_size:
                # 첫 문단이 아니면 줄바꿈 추가
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += para
            else:
                # 현재 청크가 있으면 저장
                if current_chunk:
                    chunk_end = text.find(current_chunk, current_start) + len(current_chunk)
                    chunks.append({
                        "index": len(chunks),
                        "text": current_chunk,
                        "start_char": current_start,
                        "end_char": chunk_end
                    })
                
                # 오버랩 적용 (이전 청크의 마지막 부분 포함)
                if overlap > 0 and len(current_chunk) > overlap:
                    # 온전한 문장 단위로 오버랩
                    overlap_text = PDFProcessor._get_sentence_overlap(current_chunk, overlap)
                    current_chunk = overlap_text + para
                    current_start = text.find(current_chunk, max(0, chunk_end - overlap * 2))
                else:
                    current_chunk = para
                    current_start = para_start
        
        # 마지막 청크 추가
        if current_chunk:
            chunk_end = text.find(current_chunk, current_start) + len(current_chunk)
            chunks.append({
                "index": len(chunks),
                "text": current_chunk,
                "start_char": current_start,
                "end_char": chunk_end
            })
        
        return chunks
    
    @staticmethod
    def _chunk_text(text: str, chunk_size: int, overlap: int) -> List[Dict[str, Any]]:
        """
        텍스트를 고정 크기로 청킹 (내부 메서드)
        
        Args:
            text: 텍스트
            chunk_size: 청크 크기
            overlap: 오버랩 크기
            
        Returns:
            청크 목록
        """
        chunks = []
        start = 0
        
        while start < len(text):
            # 청크 종료 위치 계산
            end = min(start + chunk_size, len(text))
            
            # 문장 단위로 조정 (가능한 경우)
            if end < len(text):
                # 문장 끝 찾기
                sentence_end = text.rfind(".", start, end)
                if sentence_end > start + chunk_size // 2:
                    end = sentence_end + 1
            
            # 청크 추출
            chunk_text = text[start:end]
            
            chunks.append({
                "text": chunk_text,
                "start_char": start,
                "end_char": end
            })
            
            # 다음 시작 위치 (오버랩 적용)
            start = max(start + chunk_size - overlap, end - overlap)
            
            # 진행이 없으면 강제로 이동
            if start >= len(text) or start <= chunks[-1]["start_char"]:
                break
        
        return chunks
    
    @staticmethod
    def _get_sentence_overlap(text: str, min_overlap: int) -> str:
        """
        문장 단위 오버랩 텍스트 가져오기
        
        Args:
            text: 원본 텍스트
            min_overlap: 최소 오버랩 크기
            
        Returns:
            오버랩 텍스트
        """
        if not text or len(text) <= min_overlap:
            return text
            
        # 문장 끝 패턴
        sentence_end_pos = [m.end() for m in re.finditer(r'[.!?]\s+', text)]
        
        # 오버랩 위치 찾기
        for pos in reversed(sentence_end_pos):
            if len(text) - pos >= min_overlap:
                return text[pos:]
        
        # 적절한 문장 끝을 찾지 못한 경우
        return text[-min_overlap:]
    
    @staticmethod
    async def process_and_embed_document(db: Session, document_id: int, user_id: int) -> Dict[str, Any]:
        """
        PDF 문서 전체 처리: 파싱 → 청크 생성 → ChromaDB에 임베딩 저장
        """
        from app.services.pdf_agent.chromadb_service import ChromaDBService
        
        db_pdf = get_pdf_by_id(db, document_id)
        if not db_pdf:
            raise ValueError(f"❌ Document with ID {document_id} not found")

        # 1. 문서 파싱
        parsed = await PDFProcessor.parse_document(db_pdf)
        if not parsed.get("success"):
            raise ValueError(f"❌ Parsing failed: {parsed.get('error')}")

        # 2. 청크 생성
        chunks = await PDFProcessor.chunk_document(
            text=parsed["text"],
            structure=parsed.get("structure"),
            chunk_size=settings.PDF_CHUNK_SIZE,
            overlap=settings.PDF_CHUNK_OVERLAP
        )

        # 3. ChromaDB에 저장
        chromadb_service = ChromaDBService()
        success = chromadb_service.add_document_chunks(
            user_id=user_id,
            document_id=document_id,
            chunks=chunks
        )

        return {
            "document_id": document_id,
            "chunk_count": len(chunks),
            "parsed": True,
            "embedded": success,
            "success": success
        }