from dotenv import dotenv_values
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.tools import search_documents_for_qa
import os
envs = dotenv_values(".env")
api_key = envs["OPENAI_API_KEY"]
llm = ChatOpenAI(model = "gpt-4.1-mini")

def start_point_of_qa_system(state: AgentState):
    messages = state["messages"]
    user_input = messages.pop().content

    user_id = state["user_id"]
    folder = state["folder"]  # ✅ 이 줄 추가
    query = user_input

    # 로그
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"[QA 디버그] 검색용 폴더명: {folder}, 질문: {query}")

    material = search_documents_for_qa(user_id, folder, query)

    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"검색된 자료: {material}")

    request = HumanMessage(content=f"""다음 질문에 자료를 참고하여 답변해주세요.
만약 자료의 내용으로는 설명이 불가하거나 충분하지 못하다면, 알고있는 지식을 이용하여 보충 설명해주세요.
자료 : {material}
질문 : {user_input}""")
    messages.append(request)

    result = llm.invoke(messages)  # 문자열로 변환하지 않음
    messages.append(AIMessage(content=result.content))

    return {
        "messages": messages,
        "last_assistant_response": result.content  # ✅ 응답 저장
    }