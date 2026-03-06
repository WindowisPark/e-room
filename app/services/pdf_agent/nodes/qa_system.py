from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.tools import search_documents_for_qa
from app.services.pdf_agent.prompts.qa import (
    QA_WITH_MATERIAL_PROMPT,
    QA_WITHOUT_MATERIAL_PROMPT,
)
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)
llm = ChatGoogleGenerativeAI(
    model=settings.AI_MODEL_NAME,
    google_api_key=settings.GOOGLE_API_KEY,
    request_timeout=settings.AI_LLM_TIMEOUT,
    temperature=0.4,
    max_output_tokens=2048,
)


def build_qa_messages(state: AgentState):
    """LLM에 전달할 messages 리스트와 user_input을 반환"""
    messages = list(state["messages"])
    user_input = state.get("last_user_query", "")

    has_docs = bool(
        state.get("selected_files") or
        (state.get("document_id") and state.get("document_id") != 0)
    )

    if has_docs:
        logger.info("[자료 참조 — RAG 사용]")
        material = search_documents_for_qa(
            user_id=state["user_id"],
            query=user_input,
            document_id=state.get("document_id"),
        )
        request = HumanMessage(content=QA_WITH_MATERIAL_PROMPT.format(
            material=material, user_input=user_input
        ))
    else:
        logger.info("[자료 없음 — 교육 전문 답변]")
        request = HumanMessage(content=QA_WITHOUT_MATERIAL_PROMPT.format(user_input=user_input))

    messages.append(request)
    return messages, user_input


def finalize_qa_state(messages: list, user_input: str, result: str) -> dict:
    """스트리밍/invoke 완료 후 state 업데이트"""
    messages.pop()  # 재작성 prompt 제거 (너무 김)
    messages.append(HumanMessage(content=user_input))
    messages.append(AIMessage(content=result))
    return {"messages": messages}


def start_point_of_qa_system(state: AgentState):
    messages, user_input = build_qa_messages(state)
    result = llm.invoke(messages).content
    return finalize_qa_state(messages, user_input, result)
