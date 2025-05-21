# app/services/pdf_agent/nodes/scheduler.py

from langchain_openai import ChatOpenAI
from app.services.pdf_agent.states import AgentState
from langchain_core.messages import HumanMessage
from dotenv import dotenv_values
from datetime import date
import os
import json
from app.services.pdf_agent.chromadb_service import ChromaDBService

envs = dotenv_values(".env")
api_key = envs["OPENAI_API_KEY"]
llm = ChatOpenAI(model="gpt-4.1-mini")


def start_point_of_schedule(state: AgentState):
    print("스케줄 그래프 시작")


def select_subjects(state: AgentState):
    # subjects는 이미 외부 입력을 통해 전달되므로 index 초기화만 수행
    return {"subject_index": 0}


def select_importance(state: AgentState):
    return {}  # 이미 state["importance"]로 존재


def select_deadlines(state: AgentState):
    return {}  # 이미 state["deadlines"]로 존재


def select_folder_for_schedule(state: AgentState):
    """
    과목명과 가장 관련 있는 사용자 폴더 자동 선택
    """
    user_id = state["user_id"]
    subject_index = state["subject_index"]
    subjects = state["subjects"]

    user_folder_path = f"{user_id}/chroma"
    folders = os.listdir(user_folder_path) if os.path.exists(user_folder_path) else []

    if not folders:
        raise ValueError(f"사용자 폴더가 존재하지 않음: {user_folder_path}")

    folder = llm.invoke(
        f"다음 폴더 중 '{subjects[subject_index]}' 과목과 가장 관련 있는 폴더명을 1개만 말해주세요.\n"
        f"폴더 목록: {folders}"
    ).content.strip()

    return {"folder": folder, "subject_index": subject_index + 1}


def get_all_document(state: AgentState):
    """
    선택된 폴더에서 문서를 검색하여 학습할 전체 내용 확보
    """
    folder = state["folder"]
    user_id = int(state["user_id"])

    chroma = ChromaDBService()
    chunks = chroma.search_across_documents(user_id=user_id, query_text="", folder_name=folder, limit=20)
    docs = [chunk["text"] for chunk in chunks]

    return {"docs": docs}


def define_final_index(state: AgentState):
    """
    폴더 내 모든 문서 내용을 결합 → 목차 요약 생성
    """
    docs = state["docs"]
    final_index = state["final_index"]

    full_text = "\n".join(docs)
    summary = llm.invoke(
        f"다음은 여러 문서의 목차 내용입니다. 전체 내용을 정리하여 학습 계획 수립을 위한 통합 목차를 생성해주세요.\n\n{full_text}"
    ).content

    final_index.append(summary)
    return {"final_index": final_index}


def check_sub_count(state: AgentState):
    """
    모든 과목에 대해 폴더 선택 및 목차 생성을 완료했는지 확인
    """
    if state["subject_index"] >= len(state["subjects"]):
        return "completion"
    return "continue"


def make_plans(state: AgentState):
    """
    과목별 목차/중요도/마감일 기반 학습 계획 수립
    """
    subjects = state["subjects"]
    final_index = state["final_index"]
    importances = state["importance"]
    deadlines = state["deadlines"]
    today = date.today()

    subject_data = {
        sub: {
            "목차": idx,
            "중요도": imp,
            "마감일": dl
        }
        for sub, idx, imp, dl in zip(subjects, final_index, importances, deadlines)
    }

    example_format = {
        "2025-06-01": {
            "과목1": {
                "학습할 범위": "1~2단원",
                "예상 학습 시간": "3시간"
            }
        }
    }

    result = llm.invoke(
        f"""
        아래는 과목별 학습 정보입니다.
        각 과목의 목차 양, 중요도, 마감일, 현재 날짜를 고려하여 학습 계획표를 JSON 형식으로 만들어주세요.
        최대 학습 시간: 하루 9시간.
        마감일 전날은 해당 과목 학습에 더 많은 시간을 할당해주세요.

        반환 형식은 다음을 따라주세요:
        {example_format}

        오늘 날짜: {today}
        내용: {json.dumps(subject_data, ensure_ascii=False)}
        """
    ).content

    return {"schedule": result}


def save_plan(state: AgentState):
    """
    JSON 형식 학습 계획을 파일로 저장 + 메시지에 첨부
    """
    schedule = state["schedule"]
    user_id = state["user_id"]
    user_dir = f"{user_id}/schedule"
    os.makedirs(user_dir, exist_ok=True)
    file_index = len(os.listdir(user_dir)) + 1
    file_path = os.path.join(user_dir, f"schedule_{file_index}.json")

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(schedule, f, ensure_ascii=False, indent=2)

    messages = state["messages"]
    messages.append(HumanMessage(content=schedule))

    return {"messages": messages}
