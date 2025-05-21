# app/services/pdf_agent/nodes/qa_system.py

from dotenv import dotenv_values
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from gptpdf import parse_pdf
from opensearchpy import OpenSearch
from app.services.pdf_agent.states import AgentState
# tools 모듈에서 search_documents_for_qa 가져오기 추가
from app.services.pdf_agent.tools import search_documents_for_qa, search_documents_for_exam
import os

envs = dotenv_values(".env")
api_key = envs["OPENAI_API_KEY"]
llm = ChatOpenAI(model="gpt-4.1-mini")

def start_point_of_qa_system(state: AgentState) -> dict:
    messages = state["messages"]
    user_input = messages.pop().content
    # 이제 search_documents_for_qa 함수를 올바르게 가져와서 사용
    material = search_documents_for_qa(state["user_id"], state["folder"], user_input)
    request = HumanMessage(content=f"""다음 질문에 자료를 참고하여 답변해주세요.\n
                                       만약 자료의 내용으로는 설명이 불가하거나 충분하지 못하다면, 알고있는 지식을 이용하여 보충 설명해주세요.\n
                                        자료 : {material}
                                       질문 : {user_input}""")
    messages.append(request)
    result = llm.invoke(f"{messages}")
    messages.append(AIMessage(content=result.content))

    return {"messages": messages}