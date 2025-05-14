import time
import logging

# 로깅 설정
logger = logging.getLogger('pdf_tasks')

def process_pdf_simple(document_id: int):
    """
    간단한 PDF 처리 시뮬레이션 함수
    실제 DB 액세스 없이 작업 큐 테스트용
    
    Args:
        document_id: 처리할 PDF 문서 ID
        
    Returns:
        처리 결과
    """
    logger.info(f'PDF 처리 시작: 문서 ID {document_id}')
    
    # 처리 시간 시뮬레이션
    for i in range(5):
        time.sleep(1)
        logger.info(f'PDF 처리 진행 중: {(i+1)*20}% 완료')
    
    result = {
        "success": True,
        "document_id": document_id,
        "processed_pages": 10,
        "extracted_text_length": 5000,
        "processing_time": 5
    }
    
    logger.info(f'PDF 처리 완료: 문서 ID {document_id}')
    return result
