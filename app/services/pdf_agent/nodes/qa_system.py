# app/services/pdf_agent/nodes/qa_system.py

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.chromadb_service import ChromaDBService
import logging

llm = ChatOpenAI(model="gpt-4.1-mini")
logger = logging.getLogger(__name__)

def start_point_of_qa_system(state: AgentState) -> dict:
    messages = state.get("messages", [])
    user_input = state.get("last_user_query", "")

    # ✅ ChromaDB에서 문서 검색
    chroma = ChromaDBService()
    material_chunks = chroma.search_across_documents(
        user_id=int(state["user_id"]),
        query_text=user_input,
        folder_name=state["folder"],
        limit=3
    )

    logger.info(f"[QA] 사용자 질문: {user_input}")
    logger.info(f"[QA] 검색된 문서 수: {len(material_chunks)}")

    if not material_chunks:
        logger.warning("[QA] 관련 문서 없음 → 일반 지식 기반 응답 시도")

    # ✅ 텍스트 병합
    combined_text = "\n\n".join(chunk["text"] for chunk in material_chunks)

    # ✅ 프롬프트 구성
    prompt = f"""다음 질문에 자료를 참고하여 답변해주세요.
만약 자료의 내용으로는 설명이 불가하거나 충분하지 못하다면, 알고있는 지식을 이용하여 보충 설명해주세요.

자료 : {combined_text}
질문 : {user_input}
"""

    # ✅ 메시지 구성 및 LLM 호출
    messages.append(HumanMessage(content=prompt))
    result = llm.invoke(messages)
    messages.append(AIMessage(content=result.content))

    logger.info(f"[QA] LLM 응답 길이: {len(result.content)}")
    logger.debug(f"[QA] LLM 응답 내용: {result.content[:500]}...")

    return {
        "messages": messages,
        "last_assistant_response": result.content
    }
