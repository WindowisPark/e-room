# app/services/pdf_agent/tools.py

from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage
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

def search_documents_for_qa(user_id: str, query: str, document_id: int = None, k: int = 5):
    """
    ChromaDBService를 통해 사용자 문서에서 쿼리와 관련된 청크를 검색합니다.

    Args:
        user_id: 사용자 ID
        query: 검색 쿼리
        document_id: 특정 문서 ID (없으면 전체 문서 검색)
        k: 반환할 결과 수

    Returns:
        검색 결과 청크 리스트
    """
    from app.services.pdf_agent.chromadb_service import ChromaDBService
    service = ChromaDBService()
    if document_id:
        return service.search_similar_chunks(int(user_id), document_id, query, limit=k)
    else:
        return service.search_across_documents(int(user_id), query, limit=k)