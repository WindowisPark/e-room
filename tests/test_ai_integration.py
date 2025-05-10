# tests/test_ai_integration.py

import os
import sys
import logging
from dotenv import load_dotenv

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# .env 파일 로드 (프로젝트 루트 디렉토리에 있다고 가정)
load_dotenv()

# API 키 확인 - .env 파일에서 로드됨
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    logger.warning("OPENAI_API_KEY가 .env 파일에 설정되지 않았습니다.")
    # 기본값 또는, 대체 환경 변수를 설정하려면 아래 줄의 주석을 해제하세요
    # os.environ["OPENAI_API_KEY"] = "기본값" 

# 모듈 경로 추가 (필요한 경우)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 파일 경로 설정 - pdf_agent 폴더 내의 test.pdf
pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'services', 'pdf_agent', 'test.pdf'))
logger.info(f"테스트할 PDF 경로: {pdf_path}")

# AI 서비스 임포트
from app.services.pdf_agent.ai_service import PDFAIService

def test_pdf_processing():
    """PDF 처리 테스트"""
    
    # 서비스 초기화
    service = PDFAIService()
    
    # 서비스 호출
    logger.info(f"PDF 처리 시작: {pdf_path}")
    result = service.process_pdf(pdf_path)
    
    # 결과 확인
    if result.get("success", False):
        logger.info("PDF 처리 성공!")
        logger.info(f"결과 길이: {len(result['result'])}")
        logger.info(f"결과 미리보기: {result['result'][:200]}...")
    else:
        logger.error(f"PDF 처리 실패: {result.get('error', '알 수 없는 오류')}")
    
    return result

def test_exam_generation():
    """시험 문제 생성 테스트"""
    
    # 서비스 초기화
    service = PDFAIService()
    
    # 서비스 호출
    logger.info(f"문제 생성 시작: {pdf_path}")
    result = service.generate_exam(pdf_path, 3)  # 3개 문제 생성
    
    # 결과 확인
    if result.get("success", False):
        logger.info("문제 생성 성공!")
        logger.info(f"생성된 문제: {result['questions']}")
    else:
        logger.error(f"문제 생성 실패: {result.get('error', '알 수 없는 오류')}")
    
    return result

if __name__ == "__main__":
    # API 키가 없으면 테스트를 종료
    if not api_key:
        logger.error("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일을 확인하세요.")
        sys.exit(1)
        
    # 테스트 실행
    logger.info("=== PDF 처리 테스트 시작 ===")
    pdf_result = test_pdf_processing()
    
    logger.info("\n=== 문제 생성 테스트 시작 ===")
    exam_result = test_exam_generation()
    
    logger.info("\n=== 테스트 완료 ===")