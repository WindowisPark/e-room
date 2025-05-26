# app/services/pdf_agent/nodes/scheduler.py

from dotenv import dotenv_values
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from datetime import date
import os
import json

from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.tools import get_all_docs  # ✅ ChromaDBService 대체

envs = dotenv_values(".env")
api_key = envs["OPENAI_API_KEY"]
llm = ChatOpenAI(model="gpt-4.1-mini")

def start_point_of_schedule(state: AgentState):
    print("스케줄 그래프 시작")

def select_subjects(state: AgentState):
    return {"subject_index": 0, "subjects": ["정보보호", "네트워크"]}

def select_importance(state: AgentState):
    return {}

def select_deadlines(state: AgentState):
    return {}
def get_all_document(state : AgentState):
    subjects = state["subjects"]
    docs=[]
    for subject in subjects: #
        docs.append(get_all_docs(subject))

    return {"docs":docs}

def define_final_index(state: AgentState):
    docs = state["docs"]
    final_index = []
    
    for doc in docs:
        final_index.append(
            llm.invoke(f"다음 내용은 여러 파일에 대한 목차들을 합친 내용입니다.\n다음 내용을 정리하여 전체 내용을 포함하는 목차를 생성해주세요. \n전체 내용 : {doc}").content)

    return {"final_index":final_index}

def check_sub_count(state: AgentState):
    subject_index = state["subject_index"]
    
    if subject_index == len(state["subjects"]):
        return "completion"
    else:
        return "continue"
    
def make_plans(state: AgentState):
    subjects = state["subjects"]
    final_index = state["final_index"]
    importances = state["importance"]
    today = date.today()
    deadlines = state["deadlines"]
    
    total_file = {}
    for sub,idx,importance,deadline in zip(subjects,final_index,importances,deadlines):
        total_file[sub]={
            "목차" : idx,
            "중요도" : importance,
            "마감일" : deadline
        }
    example = {
        "날짜" : {
            "과목" : {
                "학습할 범위" : "~~~",
                "예상 학습 시간" : "~~",
            },
            "과목2" :{
            },
        },	
    }

    result = llm.invoke(
        f"""다음 제공된 내용을 보고 시험기간 학습 계획표를 작성해주세요\n
        다음 내용은 과목별 목차, 중요도, 마감일 정보를 가집니다.\n
        학습 계획은 3가지를 고려해야 합니다.\n
        1. 각 과목 목차의 양\n
        2. 각 과목의 중요도\n
        3. 오늘 날짜로부터 마감일까지의 기간\n

        최대 가용시간 9시간을 모두 활용하도록 적절하게 학습 계획을 세워주시고, 그 내용은 자세하게 어떤 내용을 어떻게 공부해야 하는지 안내해주셔야 합니다.\n
        목차만 간단하게 말하는 것이 아니라 이 부분을 어떤식으로 학습한다는 것을 알려주시면 좋을 것 같습니다.

        시험 전날(마감일)에는 다음날 시험인 과목의 비중을 높여주어야 합니다.

        학습 계획은 다른 내용없이 오로지 다음과 같은 json 구조로 출력하여 즉시 json으로 이용이 가능하도록 출력해주셔야 합니다.

        구조 : {example}

        내용 : {total_file}
        """
    ).content

    print("[result]\t"+"=="*40)
    print(result)

    return {"schedule": result}

def save_plan(state: AgentState):
    schedule = state["schedule"]
    user_id = state["user_id"]
    user_dir = f"{user_id}/schedule" 
    os.makedirs(user_dir, exist_ok=True)
    number_of_files = len(os.listdir(user_dir))
    schedule_data = json.loads(schedule)
    with open(os.path.join(user_dir, f"schedule_{number_of_files+1}.json"), "w", encoding="utf-8") as json_file:
        json.dump(schedule_data, json_file, ensure_ascii=False, indent=4)
    
    messages = state["messages"]
    messages.append(AIMessage(content=schedule))
    return {"message":messages}