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

def start_point_of_qa_system(state: AgentState):
    messages = list(state["messages"])
    user_input = messages[-1].content
    messages = messages[:-1]  # 마지막 user 메시지 제거 (재작성 prompt로 대체)

    # check_reference LLM call 제거 → 파일/문서 여부로 직접 판단
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
    result = llm.invoke(f"{messages}").content
    messages.pop()  # 재작성 prompt 제거 (너무 김)
    messages.append(HumanMessage(content=f"{user_input}"))
    messages.append(AIMessage(content=result))
    return {"messages": messages}
