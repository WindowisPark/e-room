# app/services/pdf_agent/processor.py

from gptpdf import parse_pdf
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List, Dict, Any
import os
from app.services.pdf_agent.chromadb_service import ChromaDBService

class PDFProcessor:
    """
    GPTPDF 기반으로 리팩토링된 PDF 처리기
    - 텍스트 + 이미지 추출
    - 청크 분할
    - ChromaDB 저장
    """

    @staticmethod
    def parse_and_split(pdf_path: str, chunk_size: int = 3000, chunk_overlap: int = 200) -> Dict[str, Any]:
        content, images = parse_pdf(
            pdf_path=pdf_path,
            model="gpt-4.1-mini",
            api_key=os.getenv("OPENAI_API_KEY"),
            output_path="./images"
        )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len
        )
        chunks = splitter.split_documents([Document(page_content=content)])

        return {
            "text": content,
            "images": images,
            "chunks": chunks
        }

    @staticmethod
    def store_chunks(user_id: int, document_id: int, folder: str, chunks: List[Document]) -> bool:
        chroma_service = ChromaDBService()
        prepared_chunks = []

        for i, chunk in enumerate(chunks):
            prepared_chunks.append({
                "index": i,
                "text": chunk.page_content,
                "start_char": 0,
                "end_char": len(chunk.page_content),
                "page": 1
            })

        return chroma_service.add_document_chunks(user_id, document_id, folder, prepared_chunks)
