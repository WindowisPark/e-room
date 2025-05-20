# app/services/pdf_agent/tools.py

from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import os
import logging
from dotenv import load_dotenv
from app.core.config import settings

# 로깅 설정
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY", "")

def get_initial_state() -> Dict[str, Any]:
    """
    LangGraph 초기 상태 생성
    
    Returns:
        초기화된 상태 딕셔너리
    """
    return {
        "messages": [
            SystemMessage(content="""당신은 학생들을 가르치는 것으로 국내 0.1%의 명성을 가진 교육자입니다.
            다음 사용자의 요청에 따라 작업을 수행해주시면 됩니다. 사용자의 요청은 총 4가지로 이루어져 있습니다.
            1. 질의 응답, 2. 학습 자료 요약, 3. 시험 문제 생성, 4. 학습 계획 세우기입니다.
            특히 질의 응답의 경우, 자료에 근거하여 답변해주시되, 질문에 답하기 위한 좋은 자료가 존재하지 않다면, 당신이 아는 지식으로 답변해주시면 됩니다.
            사용자의 요청에 친절하고 자세한 설명으로 국내 0.1% 명성에 맞게 학습자의 이해를 도와주시면 됩니다.""")
        ],
        "last_user_query": "",      # 마지막 사용자 질문
        "last_assistant_response": "", # 마지막 응답
        "user_id": "",               # 처리 중 설정될 사용자 ID
        "purpose": "",               # 사용자 요청 목적 (summary, qa_system 등)
        "document_id": None,         # 처리할 문서 ID
        "folder": "default",         # 저장 폴더
        "pdf_text": "",              # 추출된 PDF 텍스트
        "structure": {},             # 문서 구조 정보
        "doc_chunks": [],            # 분할된 청크 (pdfs 대신 사용)
        "summaries": "",             # 요약 결과 저장
        "result": "",                # 최종 결과 저장
        "explain_step": 0,           # 설명 단계 카운터
        "need_to_explain": {},       # 설명 필요 항목
        "subject_index": 0,          # 과목 인덱스
        "final_index": [],           # 최종 인덱스 목록
        "personality": [],           # 출제자 성향 목록
        "final_personality": "",     # 최종 출제자 성향
        "embedding_stored": False,   # 임베딩 저장 완료 여부
        "error": None                # 오류 메시지
    }


def search_documents_for_qa(user_id: str, folder: str, query: str, k: int = 2) -> List[Dict[str, Any]]:
    """
    질의응답을 위한 문서 검색
    
    Args:
        user_id: 사용자 ID
        folder: 폴더명
        query: 검색 쿼리
        k: 반환할 결과 수
        
    Returns:
        관련 문서 목록
    """
    try:
        # 사용자 ChromaDB 경로
        user_dir = f"{user_id}/chroma/{folder}"
        
        # 경로 존재 확인
        if not os.path.exists(user_dir):
            logger.warning(f"사용자 ChromaDB 경로가 존재하지 않음: {user_dir}")
            return []
        
        # 임베딩 모델 초기화
        embeddings = OpenAIEmbeddings(api_key=API_KEY)
        
        # ChromaDB 로드
        vectorstore = Chroma(persist_directory=user_dir, embedding_function=embeddings)
        
        # 유사도 검색 실행
        results = vectorstore.similarity_search_with_score(
            query, 
            k=k, 
            filter={"is_full_document": False}
        )
        
        # 결과 필터링 및 반환
        return [doc for doc, score in results if score < 0.8]  # 점수가 낮을수록 유사도 높음
        
    except Exception as e:
        logger.error(f"문서 검색 실패: {str(e)}")
        return []


def search_documents_for_summary(user_id: str, folder: str, query: str = None, k: int = 1) -> List[Dict[str, Any]]:
    """
    요약을 위한 문서 검색
    
    Args:
        user_id: 사용자 ID
        folder: 폴더명
        query: 검색 쿼리 (선택 사항)
        k: 반환할 결과 수
        
    Returns:
        관련 문서 목록
    """
    try:
        # 사용자 ChromaDB 경로
        user_dir = f"{user_id}/chroma/{folder}"
        
        # 경로 존재 확인
        if not os.path.exists(user_dir):
            logger.warning(f"사용자 ChromaDB 경로가 존재하지 않음: {user_dir}")
            return []
        
        # 임베딩 모델 초기화
        embeddings = OpenAIEmbeddings(api_key=API_KEY)
        
        # ChromaDB 로드
        vectorstore = Chroma(persist_directory=user_dir, embedding_function=embeddings)
        
        # 전체 문서 검색
        if query:
            # 쿼리가 있는 경우 유사도 검색
            results = vectorstore.similarity_search(
                query, 
                k=k, 
                filter={"is_full_document": True}
            )
        else:
            # 쿼리가 없는 경우 모든 전체 문서 가져오기
            results = vectorstore.get(filter={"is_full_document": True})
            
        return results
        
    except Exception as e:
        logger.error(f"요약용 문서 검색 실패: {str(e)}")
        return []


def search_documents_for_exam(user_id: str, folder: str) -> List[Dict[str, Any]]:
    """
    시험 문제 생성을 위한 문서 검색
    
    Args:
        user_id: 사용자 ID
        folder: 폴더명
        
    Returns:
        문서 목록
    """
    try:
        # 사용자 ChromaDB 경로
        user_dir = f"{user_id}/chroma/{folder}"
        
        # 경로 존재 확인
        if not os.path.exists(user_dir):
            logger.warning(f"사용자 ChromaDB 경로가 존재하지 않음: {user_dir}")
            return []
        
        # 임베딩 모델 초기화
        embeddings = OpenAIEmbeddings(api_key=API_KEY)
        
        # ChromaDB 로드
        vectorstore = Chroma(persist_directory=user_dir, embedding_function=embeddings)
        
        # 전체 문서 가져오기
        documents = vectorstore.get(filter={"is_full_document": True})
        
        return documents
        
    except Exception as e:
        logger.error(f"시험용 문서 검색 실패: {str(e)}")
        return []


def search_documents_for_scheduler(user_id: str, folder: str) -> List[Dict[str, Any]]:
    """
    학습 계획 생성을 위한 문서 검색
    
    Args:
        user_id: 사용자 ID
        folder: 폴더명
        
    Returns:
        문서 목록
    """
    try:
        # 사용자 ChromaDB 경로
        user_dir = f"{user_id}/chroma/{folder}"
        
        # 경로 존재 확인
        if not os.path.exists(user_dir):
            logger.warning(f"사용자 ChromaDB 경로가 존재하지 않음: {user_dir}")
            return []
        
        # 임베딩 모델 초기화
        embeddings = OpenAIEmbeddings(api_key=API_KEY)
        
        # ChromaDB 로드
        vectorstore = Chroma(persist_directory=user_dir, embedding_function=embeddings)
        
        # 인덱스 정보가 있는 문서 검색
        documents = vectorstore.get(filter={"indices": True})
        
        return documents
        
    except Exception as e:
        logger.error(f"스케줄러용 문서 검색 실패: {str(e)}")
        return []