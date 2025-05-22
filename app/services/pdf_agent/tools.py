# app/services/pdf_agent/tools.py

from typing import Dict, Any, Optional
from langchain_core.messages import SystemMessage
from dotenv import dotenv_values
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma


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
        "error": None
    }

def search_documents_by_purpose(
    user_id: str,
    folder: str,
    purpose: str,
    query: Optional[str] = ""
) -> list:
    if purpose == "summary":
        return search_documents_for_summary(user_id, folder, query)
    elif purpose == "qa_system":
        return search_documents_for_qa(user_id, folder, query)
    elif purpose == "generate_exam":
        return search_documents_for_exam(user_id, folder)
    elif purpose == "schedule":
        return search_documents_for_scheduler(user_id, folder)
    else:
        return []

def search_documents_for_qa(user_id: str, folder: str, query: str, k: int = 2):
    envs = dotenv_values(".env")
    api_key = envs["OPENAI_API_KEY"]
    user_dir = f"{user_id}/chroma/{folder}"
    embeddings = OpenAIEmbeddings(api_key=api_key)
    vectorstore = Chroma(persist_directory=user_dir, embedding_function=embeddings)
    results = vectorstore.similarity_search_with_score(query, k=k, filter={"is_full_document": False})

    # 🔍 유사도 로그 출력
    import logging
    logger = logging.getLogger(__name__)
    for doc, score in results:
        logger.info(f"[QA 유사도] score={score:.4f}, preview={doc.page_content[:50]}")

    # 🔧 점수 기준 완화
    return [doc for doc, score in results if score >= 0.2]

def search_documents_for_summary(user_id: str, folder: str, query: str, k: int = 2):
    envs = dotenv_values(".env")
    api_key = envs["OPENAI_API_KEY"]
    user_dir = f"{user_id}/chroma/{folder}"
    embeddings = OpenAIEmbeddings(api_key=api_key)
    vectorstore = Chroma(persist_directory=user_dir, embedding_function=embeddings)
    return vectorstore.similarity_search(query, k=k, filter={"is_full_document": True})

def search_documents_for_scheduler(user_id: str, folder: str, k: int = 2):
    envs = dotenv_values(".env")
    api_key = envs["OPENAI_API_KEY"]
    user_dir = f"{user_id}/chroma/{folder}"
    embeddings = OpenAIEmbeddings(api_key=api_key)
    vectorstore = Chroma(persist_directory=user_dir, embedding_function=embeddings)
    return vectorstore.get(where={"indices": True})

def search_documents_for_exam(user_id: str, folder: str):
    envs = dotenv_values(".env")
    api_key = envs["OPENAI_API_KEY"]
    user_dir = f"{user_id}/chroma/{folder}"
    embeddings = OpenAIEmbeddings(api_key=api_key)
    vectorstore = Chroma(persist_directory=user_dir, embedding_function=embeddings)
    return vectorstore.get(where={"is_full_document": True})
