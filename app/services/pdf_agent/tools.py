# app/services/pdf_agent/tools.py (완전 수정 버전)

from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage
from dotenv import dotenv_values
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PDFPlumberLoader
from app.core.config import settings
import logging
import os

logger = logging.getLogger(__name__)

def get_initial_state(
    user_id: str,
    document_id: int,
    pdf_path: str,
    purpose: str,
    folder: str = "default",
    query: Optional[str] = ""
) -> Dict[str, Any]:
    """
    LangGraph 초기 상태 생성
    """
    return {
        "messages": [
            SystemMessage(content="""당신은 학생들을 가르치는 것으로 국내 0.1%의 명성을 가진 교육자입니다.
            다음 사용자의 요청에 따라 작업을 수행해주시면 됩니다. 사용자의 요청은 총 4가지로 이루어져 있습니다.
            1. 질의 응답, 2. 학습 자료 요약, 3. 시험 문제 생성, 4. 학습 계획 세우기입니다.
            특히 질의 응답의 경우, 자료에 근거하여 답변해주시되, 질문에 답하기 위한 좋은 자료가 존재하지 않다면, 당신이 아는 지식으로 답변해주시면 됩니다.
            사용자의 요청에 친절하고 자세한 설명으로 국내 0.1% 명성에 맞게 학습자의 이해를 도와주시면 됩니다.""")
        ],
        "last_user_query": query,
        "last_assistant_response": "",
        "user_id": user_id,
        "document_id": document_id,
        "pdf_path": pdf_path,
        "purpose": purpose,
        "folder": folder,
        "pdf_text": "",
        "structure": {},
        "doc_chunks": [],
        "summaries": "",
        "result": "",
        "explain_step": 0,
        "need_to_explain": {},
        "subject_index": 0,
        "final_index": [],
        "personality": [],
        "final_personality": "",
        "embedding_stored": False,
        "error": None,
        "subjects": [],
        "importance": {},
        "deadlines": {},
        "schedule": {},
        "exam_step": "start",
        "scheduler_step": "start",
        "selected_files": [],
        "previous_exam_path": [],
        "exam_docs_path": "",
        "exam_docs": "",
        "concepts_for_exam": [],
        "problems": [],
        "docs": [],
        "pdf_content": "",
        "pdfs": []
    }

from app.services.s3_file_service import S3StorageManager

def get_all_docs(file_path: str):
    """PDF 파일에서 모든 텍스트 추출 (로컬 + S3 지원)"""
    try:
        local_path = file_path

        if not os.path.exists(file_path):
            if file_path.startswith("users/"):
                s3 = S3StorageManager()
                local_path = s3.download_to_tempfile(file_path)
            else:
                raise FileNotFoundError(f"지원되지 않는 경로: {file_path}")

        loader = PDFPlumberLoader(file_path=local_path)
        docs = loader.load()
        return "".join(doc.page_content for doc in docs)

    except Exception as e:
        logger.error(f"PDF 로드 실패: {str(e)}")
        return ""

def search_documents_for_qa(user_id: str, query: str, k: int = 5):
    """
    질문을 위해 사용자의 ChromaDB에서 쿼리와 관련된 문서를 검색하는 함수
    """
    try:
        # 환경 변수 로드
        envs = dotenv_values(".env")
        api_key = envs.get("OPENAI_API_KEY") or settings.AI_API_KEY
        
        if not api_key:
            logger.error("OpenAI API 키가 설정되지 않음")
            return []
        
        # ChromaDB 경로
        user_dir = f"{settings.CHROMADB_STORAGE_PATH}/{user_id}"
        logger.info(f"ChromaDB 검색 경로: {user_dir}")
        
        # 임베딩 모델 초기화
        embeddings = OpenAIEmbeddings(api_key=api_key)
        
        # ChromaDB 로드
        vectorstore = Chroma(persist_directory=user_dir, embedding_function=embeddings)
        
        # 유사도 검색 실행
        results = vectorstore.similarity_search_with_score(query, k=k)
        
        logger.info(f"검색 결과: {len(results)}개 문서 발견")
        return results
        
    except Exception as e:
        logger.error(f"ChromaDB 검색 실패: {str(e)}")
        return []