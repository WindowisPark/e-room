from typing import Dict, List, Any, Optional, Tuple
import os
import tempfile
import logging
import re
import json
import shutil
from datetime import datetime
import pdfplumber
from pdf2image import convert_from_path
import pytesseract

from app.core.config import settings
from app.models.tag import PDFFile

logger = logging.getLogger(__name__)

class PDFProcessor:
    """
    PDF 문서 처리 및 분석 담당 클래스
    - 문서 파싱, 청킹, 메타데이터 및 구조 정보 추출
    """

    @staticmethod
    def _extract_text_with_fallback(file_path: str) -> Tuple[str, bool]:
        """
        PDF에서 텍스트 추출 - 여러 방법 시도
        
        Args:
            file_path: PDF 파일 경로
            
        Returns:
            (추출된 텍스트, 스캔된 문서 여부) 튜플
        """
        try:
            logger.info(f"PDF 텍스트 추출 시작: {file_path}")
            
            # 파일 존재 확인
            if not os.path.exists(file_path):
                logger.error(f"파일이 존재하지 않음: {file_path}")
                return "", True
                
            # 먼저 pdfplumber 시도
            try:
                with pdfplumber.open(file_path) as pdf:
                    all_text = ""
                    is_scanned = True
                    
                    for i, page in enumerate(pdf.pages):
                        try:
                            page_text = page.extract_text() or ""
                            all_text += page_text + "\n\n"
                            
                            # 페이지 로깅
                            logger.debug(f"페이지 {i+1} 텍스트 길이: {len(page_text)} 문자")
                            
                            if page_text.strip():
                                is_scanned = False
                        except Exception as page_err:
                            logger.warning(f"페이지 {i+1} 처리 중 오류: {str(page_err)}")
                    
                    # pdfplumber 결과 확인
                    logger.info(f"pdfplumber로 추출한 텍스트 길이: {len(all_text)}, 스캔여부: {is_scanned}")
                    
                    if len(all_text.strip()) > 100 or not is_scanned:
                        return all_text, False
                        
            except Exception as plumber_err:
                logger.warning(f"pdfplumber 오류, OCR로 대체: {str(plumber_err)}")
                
            # OCR 시도 (pdfplumber가 실패하거나 텍스트가 거의 없는 경우)
            logger.info("OCR 텍스트 추출 시도 중...")
            try:
                text_from_ocr = ""
                is_scanned = True
                
                # PDF를 이미지로 변환
                images = convert_from_path(file_path, dpi=300)
                logger.info(f"PDF를 {len(images)}개 이미지로 변환 완료")
                
                for i, image in enumerate(images):
                    try:
                        page_text = pytesseract.image_to_string(image, lang='kor+eng')
                        text_from_ocr += page_text + "\n\n"
                        logger.debug(f"OCR 페이지 {i+1} 텍스트 길이: {len(page_text)} 문자")
                    except Exception as ocr_page_err:
                        logger.warning(f"OCR 페이지 {i+1} 처리 중 오류: {str(ocr_page_err)}")
                
                logger.info(f"OCR로 추출한 텍스트 길이: {len(text_from_ocr)}")
                return text_from_ocr, is_scanned
                
            except Exception as ocr_err:
                logger.error(f"OCR 텍스트 추출 실패: {str(ocr_err)}")
                return "", True

        except Exception as e:
            logger.error(f"텍스트 추출 총괄 실패: {str(e)}", exc_info=True)
            return "", True

    @staticmethod
    async def chunk_document(
        text: str,
        structure: Optional[Dict[str, Any]] = None,
        chunk_size: int = None,
        overlap: int = None
    ) -> List[Dict[str, Any]]:
        chunk_size = chunk_size or settings.PDF_CHUNK_SIZE
        overlap = overlap or settings.PDF_CHUNK_OVERLAP

        if not text or len(text.strip()) == 0:
            return []

        if structure and structure.get("sections"):
            return PDFProcessor._chunk_by_sections(text, structure["sections"], chunk_size, overlap)

        return PDFProcessor._chunk_by_paragraphs(text, chunk_size, overlap)

    @staticmethod
    def _optimize_pdf(input_path: str, output_path: str) -> bool:
        try:
            shutil.copy(input_path, output_path)
            return True
        except Exception as e:
            logger.error(f"PDF 최적화 실패: {str(e)}")
            return False

    @staticmethod
    def _extract_text_with_fallback(file_path: str) -> Tuple[str, bool]:
        try:
            with pdfplumber.open(file_path) as pdf:
                all_text = ""
                is_scanned = True

                for page in pdf.pages:
                    page_text = page.extract_text() or ""
                    all_text += page_text + "\n\n"
                    if page_text.strip():
                        is_scanned = False

                if len(all_text.strip()) > 100 or not is_scanned:
                    return all_text, False

            text_from_ocr = ""
            is_scanned = True
            images = convert_from_path(file_path, dpi=300)

            for image in images:
                page_text = pytesseract.image_to_string(image, lang='kor+eng')
                logger.debug(f"OCR 추출 텍스트 (일부): {page_text[:100]}")
                text_from_ocr += page_text + "\n\n"

            logger.info(f"OCR 추출 텍스트 총 길이: {len(text_from_ocr)}")

            return text_from_ocr, is_scanned

        except Exception as e:
            logger.error(f"텍스트 추출 실패: {str(e)}")
            return "", True

    @staticmethod
    def _extract_metadata(file_path: str) -> Dict[str, Any]:
        try:
            with pdfplumber.open(file_path) as pdf:
                file_size = os.path.getsize(file_path)
                page_count = len(pdf.pages)
                pdf_meta = pdf.metadata or {}

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
        try:
            structure = {"sections": []}
            with pdfplumber.open(file_path) as pdf:
                all_pages_text = []
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text() or ""
                    all_pages_text.append(page_text)
                    lines = page_text.split("\n")
                    for line_index, line in enumerate(lines):
                        line = line.strip()
                        if (line and len(line) < 100 and
                            (line.isupper() or re.match(r"^(?:CHAPTER|Chapter|Section|\d+\.|\d+\s|\*|\[\d+\])\s", line))):
                            structure["sections"].append({
                                "title": line,
                                "page": i + 1,
                                "index": len(structure["sections"]),
                                "start_char": sum(len(t) for t in all_pages_text[:i]) + sum(len(l) for l in lines[:line_index]),
                            })
            return structure
        except Exception as e:
            logger.error(f"구조 정보 추출 실패: {str(e)}")
            return {"sections": [], "error": str(e)}

    @staticmethod
    def _chunk_by_sections(text: str, sections: List[Dict[str, Any]], chunk_size: int, overlap: int) -> List[Dict[str, Any]]:
        chunks = []
        sorted_sections = sorted(sections, key=lambda x: x.get("start_char", 0))

        for i, section in enumerate(sorted_sections):
            start_pos = section.get("start_char", 0)
            end_pos = sorted_sections[i+1].get("start_char", len(text)) if i < len(sorted_sections) - 1 else len(text)
            section_text = text[start_pos:end_pos]
            section_title = section.get("title", "")

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
                sub_chunks = PDFProcessor._chunk_text(section_text, chunk_size, overlap)
                for j, sub_chunk in enumerate(sub_chunks):
                    prefix = section_title + "\n" if j == 0 else ""
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
        paragraphs = re.split(r"\n\s*\n", text)
        chunks = []
        current_chunk = ""
        current_start = 0
        last_end = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            para_start = text.find(para, last_end)
            para_end = para_start + len(para)
            last_end = para_end

            if len(current_chunk) + len(para) + 2 <= chunk_size:
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += para
            else:
                if current_chunk:
                    chunk_end = text.find(current_chunk, current_start) + len(current_chunk)
                    chunks.append({
                        "index": len(chunks),
                        "text": current_chunk,
                        "start_char": current_start,
                        "end_char": chunk_end
                    })
                if overlap > 0 and len(current_chunk) > overlap:
                    overlap_text = PDFProcessor._get_sentence_overlap(current_chunk, overlap)
                    current_chunk = overlap_text + para
                    current_start = text.find(current_chunk, max(0, chunk_end - overlap * 2))
                else:
                    current_chunk = para
                    current_start = para_start

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
        chunks = []
        start = 0
        while start < len(text):
            end = min(start + chunk_size, len(text))
            if end < len(text):
                sentence_end = text.rfind(".", start, end)
                if sentence_end > start + chunk_size // 2:
                    end = sentence_end + 1
            chunk_text = text[start:end]
            chunks.append({"text": chunk_text, "start_char": start, "end_char": end})
            start = max(start + chunk_size - overlap, end - overlap)
            if start >= len(text) or start <= chunks[-1]["start_char"]:
                break
        return chunks

    @staticmethod
    def _get_sentence_overlap(text: str, min_overlap: int) -> str:
        if not text or len(text) <= min_overlap:
            return text
        sentence_end_pos = [m.end() for m in re.finditer(r'[.!?]\s+', text)]
        for pos in reversed(sentence_end_pos):
            if len(text) - pos >= min_overlap:
                return text[pos:]
        return text[-min_overlap:]
