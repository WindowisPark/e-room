import asyncio
from app.db.session import SessionLocal
from app.services.pdf_agent.processor import PDFProcessor

def process_pdf_document(document_id: int):
    """
    PDF 문서 처리 작업 래퍼 함수
    비동기 함수를 동기 방식으로 실행하고 내부에서 DB 세션 생성
    
    Args:
        document_id: 처리할 PDF 문서 ID
        
    Returns:
        처리 결과
    """
    db = SessionLocal()  # 새 세션 생성
    try:
        # 비동기 함수를 동기적으로 실행
        result = asyncio.run(PDFProcessor.process_and_embed_document(db, document_id))
        return result
    finally:
        db.close()  # 세션 종료
