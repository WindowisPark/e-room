from langchain_core.messages import HumanMessage, AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.tools import search_documents_for_qa
from app.services.pdf_agent.prompts.qa import (
    CHECK_REFERENCE_PROMPT,
    QA_WITH_MATERIAL_PROMPT,
    QA_WITHOUT_MATERIAL_PROMPT,
)
from app.core.config import settings
import os

llm = ChatGoogleGenerativeAI(
    model=settings.AI_MODEL_NAME, google_api_key=settings.GOOGLE_API_KEY
)

def start_point_of_qa_system(state : AgentState):
    messages = state["messages"]
    user_input = messages.pop().content # user input 제거 (새로 prompt에 적용하기 위함)
    check = llm.invoke(CHECK_REFERENCE_PROMPT.format(user_input=user_input)).content
    if check == "1" :
        print("[자료 참조 필요]")
        material = search_documents_for_qa(user_id=state["user_id"],query=user_input) # user input에 따라 적절한 Document 찾기
        request = HumanMessage(content=QA_WITH_MATERIAL_PROMPT.format(material=material, user_input=user_input))
    else :
        print("[자료 참조 불필요]")
        request = HumanMessage(content=QA_WITHOUT_MATERIAL_PROMPT.format(user_input=user_input))

    messages.append(request) # 재 작성한 prompt를 추가
    result = llm.invoke(f"{messages}").content # 결과 얻기
    messages.pop() # 재 작성한 prompt 제거 (재작성 prompt는 너무 김)
    # messages.append(HumanMessage(content=f"{user_input}\n 참조한 자료의 이름 : {}"))
    messages.append(HumanMessage(content=f"{user_input}"))
    messages.append(AIMessage(content=result))
    print(result +"\n\n" )
    return {"messages":messages}