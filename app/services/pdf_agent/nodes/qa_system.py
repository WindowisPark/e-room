# app/services/pdf_agent/nodes/qa_system.py

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.chromadb_service import ChromaDBService

llm = ChatOpenAI(model="gpt-4.1-mini")

def start_point_of_qa_system(state: AgentState) -> dict:
    messages = state["messages"]
    user_input = messages.pop().content

    chroma = ChromaDBService()
    results = chroma.search_similar_chunks(
        user_id=int(state["user_id"]),
        document_id=int(state["document_id"]),
        query_text=user_input,
        limit=2
    )

    material = "\n\n".join([doc["text"] for doc in results])

    request = HumanMessage(content=f"""다음 질문에 자료를 참고하여 답변해주세요.\n
    만약 자료의 내용으로는 설명이 불가하거나 충분하지 못하다면, 알고있는 지식을 이용하여 보충 설명해주세요.\n
    자료 : {material}
    질문 : {user_input}""")

    messages.append(request)
    result = llm.invoke(messages)
    messages.append(AIMessage(content=result.content))

    return {"messages": messages}
