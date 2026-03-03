# app/services/pdf_agent/nodes/scheduler.py

from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from datetime import date
import os
import json

from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.tools import get_all_docs
from app.services.pdf_agent.prompts.scheduler import (
    DEFINE_INDEX_PROMPT,
    MAKE_PLANS_PROMPT,
)
from app.core.config import settings

llm = ChatGoogleGenerativeAI(
    model=settings.AI_MODEL_NAME, google_api_key=settings.GOOGLE_API_KEY
)

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
            llm.invoke(DEFINE_INDEX_PROMPT.format(doc=doc)).content)

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

    result = llm.invoke(
        MAKE_PLANS_PROMPT.format(total_file=total_file)
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