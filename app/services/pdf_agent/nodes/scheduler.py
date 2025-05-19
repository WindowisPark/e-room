from langchain_openai import ChatOpenAI
from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.tools import search_documents_for_exam
from dotenv import dotenv_values
from langchain_core.messages import HumanMessage
import os
from datetime import date
import json

envs = dotenv_values(".env")
api_key = envs["OPENAI_API_KEY"]
llm = ChatOpenAI(model = "gpt-4.1-mini")

def start_point_of_schedule(state : AgentState):
    print("스케쥴 그래프 시작")

def select_subjects(state: AgentState):
    subjects = input("과목명을 입력해주세요.(띄어쓰기로 구분)").split()
    return {"subjects":subjects,"subject_index":0}

def select_importance(state: AgentState):
    importance = input("과목별 중요도를 입력해주세요.(띄어쓰기로 구분)").split()
    return {"importance":importance}

def select_deadlines(state: AgentState):
    deadlines = input("과목별 마감일을 입력해주세요.(띄어쓰기로 구분)").split()
    return {"deadlines":deadlines}

def select_folder_for_schedule(state: AgentState):
    user_id = state["user_id"]
    subject_index = state["subject_index"]
    subjects = state["subjects"]
    folders = os.listdir(f"{user_id}/chroma")
    select_folder = llm.invoke(f"다음 폴더 중 가장 과목명과 관련 있는 폴더를 1개를 찾아 폴더명만 말씀해주세요.\n 폴더명 : {folders}\n 과목명 : {[subjects[subject_index]]}").content

    return {"folder":select_folder,"subject_index":subject_index+1}

def get_all_document(state : AgentState):
    folder = state["folder"]
    user_id = state["user_id"]

    docs = search_documents_for_scheduler(user_id=user_id,folder=folder)
    return {"docs":docs}

def define_final_index(state: AgentState):
    docs = state["docs"]
    final_index = state["final_index"]
    all_docs = ""
    for doc in docs:
        all_docs+= doc

    final_index.append(
        llm.invoke(f"다음 내용은 여러 파일에 대한 목차들을 합친 내용입니다.\n다음 내용을 정리하여 전체 내용을 포함하는 목차를 생성해주세요. \n전체 내용 : {all_docs}").content)

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

        최대 가용시간 9시간을 기준으로 적절하게 학습 계획을 세워주세요.

        시험 전날(마감일)에는 다음날 시험인 과목의 비중을 높여주어야 합니다.

        학습 계획은 다음과 같은 구조로 출력해주세요.

        {example}

        내용 : {total_file}
        """
    ).content


    return {"schedule": result}

def save_plan(state: AgentState):
    schedule = state["schedule"]
    user_id = state["user_id"]
    user_dir = f"{user_id}/schedule"
    os.makedirs(user_dir, exist_ok=True)
    number_of_files = len(os.listdir(user_dir))
    with open(os.path.join(user_dir,f"schedule_{number_of_files+1}.json"), "w") as json_file:
        json.dump(schedule,json_file)

    messages = state["messages"]
    messages.append(HumanMessage(content=schedule))

    return {"message":messages}