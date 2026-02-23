# app/services/pdf_agent/tools.py

from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage
from dotenv import dotenv_values
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_community.document_loaders import PDFPlumberLoader



def get_initial_state(
    user_id: str,
    purpose: str,
    document_id: Optional[int] = None,
    pdf_path: Optional[str] = None,
    folder: str = "default",
    query: Optional[str] = ""
) -> Dict[str, Any]:
    return {
        "messages": [
            SystemMessage(content="""당신은 학생들을 가르치는 것으로 국내 0.1%의 명성을 가진 교육자입니다.
            사용자의 요청에 따라 요약, 질의응답, 문제 생성, 학습 계획을 수행해주세요.""")
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
        "error": None
    }

def get_all_docs(file_path: str):
    loader = PDFPlumberLoader(file_path=file_path)
    docs = loader.load()
    full_text = ""
    for doc in docs:
        full_text += doc.page_content
    return full_text

def search_documents_for_qa(user_id: str, query: str, k: int = 10):
    """
    질문을 위해 사용자의 ChromaDB에서 쿼리와 관련된 문서를 검색하는 함수
    
    Args:
        user_id: 사용자 ID
        query: 검색 쿼리
        k: 반환할 결과 수
    
    Returns:
        검색 결과 문서 리스트
    """
    # 환경 변수 로드
    envs = dotenv_values(".env")
    api_key = envs["OPENAI_API_KEY"]
    # 사용자 ChromaDB 경로
    user_dir = f"{user_id}/chroma"
    print(user_dir)
    # user_dir = f"{user_id}/chroma/{folder}"
    # 임베딩 모델 초기화
    embeddings = OpenAIEmbeddings(api_key=api_key)
    
    # ChromaDB 로드
    vectorstore = Chroma(persist_directory=user_dir, embedding_function=embeddings)
    
    # 유사도 검색 실행
    results = vectorstore.similarity_search_with_score(query, k=5)
    
    return results