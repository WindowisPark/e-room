from dotenv import dotenv_values
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.tools import search_documents_for_qa
import os
envs = dotenv_values(".env")
api_key = envs["OPENAI_API_KEY"]
llm = ChatOpenAI(model = "gpt-4.1-mini")

def start_point_of_qa_system(state : AgentState):
    messages = state["messages"]
    user_input = messages.pop().content # user input 제거 (새로 prompt에 적용하기 위함)
    check = llm.invoke(f"다음 질문이 자료 참조가 필요한지(전문적인 고난이도 질문), 기본적인 내재 지식으로 답변 가능(간단하거나 낮은 난이도의 질문)한지 판단하여 숫자만 답변해주세요.\n자료 참조 필요(1), 내재 지식으로 답변 가능(0)\n질문 :{user_input}").content
    if check == "1" :
        print("[자료 참조 필요]")
        material = search_documents_for_qa(user_id=state["user_id"],query=user_input) # user input에 따라 적절한 Document 찾기
        request = HumanMessage(content = f"""다음 질문에 자료를 참고하여 답변해주세요.\n  
                                        만약 자료의 내용으로는 설명이 불가하거나 충분하지 못하다면, 알고있는 지식을 이용하여 보충 설명해주세요.\n
                                            자료 : {material}
                                        질문 : {user_input}""") # 적절하게 prompt 작성
    else : 
        print("[자료 참조 불필요]")
        request = HumanMessage(content = f"""다음 질문에 성의껏 답변해주세요.\n  
                                        
                                        질문 : {user_input}""") # 적절하게 prompt 작성
        
    messages.append(request) # 재 작성한 prompt를 추가
    result = llm.invoke(f"{messages}").content # 결과 얻기
    messages.pop() # 재 작성한 prompt 제거 (재작성 prompt는 너무 김)
    # messages.append(HumanMessage(content=f"{user_input}\n 참조한 자료의 이름 : {}"))
    messages.append(HumanMessage(content=f"{user_input}"))
    messages.append(AIMessage(content=result))
    print(result +"\n\n" )
    return {"messages":messages}