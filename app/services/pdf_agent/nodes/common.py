from dotenv import dotenv_values
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI,OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from gptpdf import parse_pdf
from opensearchpy import OpenSearch
from states import AgentState
import os
envs = dotenv_values(".env")
api_key = envs["OPENAI_API_KEY"]

llm = ChatOpenAI(model= "gpt-4.1-nano")

def input_question(state: AgentState):
    question  = input("질문을 입력해주세요.")
    messages = state["messages"]
    messages.append(HumanMessage(content=question))
    return {"messages": messages}


def judge_the_purpose_of_the_input(state: AgentState):
    """
    사용자 질문의 목적을 판단하는 함수
    output : {{
        question : "운영체제 1편을 요약해달라 함.",
        purpose : "summary",
        full_document : 1
    }}
    """
    question = state["messages"][-1].content
    purpose_map = {
        "summary":{
            "question_example": "사용자가 정확하게 요약을 명시하며 요약을 요청,어떠한 문서를 요약해주어야 한다.",
            "purpose" : "요약",
            "full_document" : 1
            } ,
        "qa_system":{
            "question_example": "어떠한 질문에 대한 답변을 해주어야 한다.",
            "purpose" : "질문",
            "full_document" : 0
            } ,
        "generate_exam":{
            "question_example": "시험 문제를 생성해주어야 한다.",
            "purpose" : "문제 생성",
            "full_document" : 1
            } ,
        "schedule":{
            "question_example": "학습 계획을 세워주어야 한다.",
            "purpose" : "학습 계획",
            "full_document" : 1
            } ,
    }
    requirement = state["messages"][-1].content
    purpose = llm.invoke(f"""사용자의 질문 의도를 분석하고 purpose map을 참고하여 eval()을 이용하여 python 문법에 맞게 json형식으로 바로 변환 가능하게 json형식으로 답변해주세요.
                         출력 예시는 아래와 같습니다.
                         1) input : 운영체제 1편을 요약해주세요.
                            \noutput : {{
                                question : "운영체제 1편을 요약해달라 함.",
                                purpose : "summary",
                                full_document : 1
                            }}
                         2) input : 스파르타 때의 정치는 어떤 것들이 있어요?
                            \noutput : {{
                                question : "스파르타 시기의 정치를 물음.",
                                purpose : "qa_system",
                                full_document : 0
                            }}
               질문 : {question}
               purpose map : {purpose_map}""")
    purpose_json = eval(purpose.content)
    print(purpose_json)
    return {"purpose": purpose_json["purpose"],"full_document":purpose_json["full_document"]}

def router(state: AgentState):
    """
    사용자 목적에 맞게 graph 분기하는 함수
    """

    return state["purpose"]

def select_folder(state: AgentState):
    user_id = state["user_id"]
    messages = state["messages"]
    folders = os.listdir(f"{user_id}/chroma")
    select_folder = llm.invoke(f"다음 폴더 중 가장 질문과 관련 있는 폴더를 1개를 찾아 폴더명만 말씀해주세요.\n 폴더명 : {folders}\n질문 : {messages[-1].content}").content

    return {"folder":select_folder}
