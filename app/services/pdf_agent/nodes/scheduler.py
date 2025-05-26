# app/services/pdf_agent/nodes/scheduler.py

from dotenv import dotenv_values
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from datetime import date
import os
import json

from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.tools import search_documents_for_scheduler  # ✅ ChromaDBService 대체
from app.services.pdf_agent.utils.file_utils import save_output_file, get_file_info, cleanup_old_files
import logging

logger = logging.getLogger(__name__)
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

def select_folder_for_schedule(state: AgentState):
    """
    과목에 해당하는 폴더를 LLM으로 선택합니다.
    'subjects'가 없을 경우 명확한 에러를 발생시킵니다.
    """
    import logging
    logger = logging.getLogger(__name__)

    user_id = state["user_id"]
    subject_index = state.get("subject_index", 0)

    if "subjects" not in state:
        logger.error(f"[스케줄러] 상태에 'subjects' 키가 없습니다. 현재 상태 키: {list(state.keys())}")
        raise KeyError("'subjects' 키가 상태에 존재하지 않습니다. select_subjects 노드가 실행되지 않았을 수 있습니다.")

    subjects = state["subjects"]

    if not subjects:
        raise ValueError("subjects 필드가 비어 있습니다. select_subjects 노드가 올바르게 과목을 추출하지 못했을 수 있습니다.")

    user_folder_path = f"{user_id}/chroma"
    folders = os.listdir(user_folder_path) if os.path.exists(user_folder_path) else []

    if not folders:
        raise ValueError(f"사용자 폴더가 존재하지 않음: {user_folder_path}")

    folder = llm.invoke(
        f"다음 폴더 중 '{subjects[subject_index]}' 과목과 가장 관련 있는 폴더명을 1개만 말해주세요.\n"
        f"폴더 목록: {folders}"
    ).content.strip()

    return {
        "folder": folder,
        "subject_index": subject_index + 1
    }

def get_all_document(state: AgentState):
    folder = state["folder"]
    user_id = state["user_id"]

    chunks = search_documents_for_scheduler(user_id=user_id, folder=folder, k=20)
    docs = [chunk.page_content if hasattr(chunk, 'page_content') else chunk.get("text", "") for chunk in chunks]

    return {"docs": docs}

def define_final_index(state: AgentState):
    docs = state["docs"]
    final_index = state["final_index"]

    full_text = "\n".join(docs)
    summary = llm.invoke(
        f"다음은 여러 문서의 목차 내용입니다. 전체 내용을 정리하여 학습 계획 수립을 위한 통합 목차를 생성해주세요.\n\n{full_text}"
    ).content

    final_index.append(summary)
    return {"final_index": final_index}

def check_sub_count(state: AgentState):
    if state["subject_index"] >= len(state["subjects"]):
        return "completion"
    return "continue"

def make_plans(state: AgentState):
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
    """개선된 학습 계획 저장"""
    schedule = state["schedule"]
    user_id = state["user_id"]
    
    try:
        # ✅ 새로운 유틸리티 사용
        file_path, filename = save_output_file(
            user_id=user_id,
            task_type="schedule",
            content=schedule,  # JSON 형식으로 자동 저장됨
            file_format="json"
        )
        
        # 파일 정보 가져오기
        file_info = get_file_info(file_path)
        
        # 오래된 파일 정리 (최신 3개만 유지)
        deleted_count = cleanup_old_files(user_id, "schedule", keep_count=3)
        if deleted_count > 0:
            logger.info(f"스케줄 파일 {deleted_count}개 정리됨 (사용자: {user_id})")
        
        logger.info(f"스케줄 파일 저장 완료: {file_path}")
        
        # 메시지에 스케줄 내용 추가
        messages = state["messages"]
        schedule_summary = f"학습 계획이 생성되었습니다!\n파일 위치: {filename}"
        messages.append(HumanMessage(content=schedule_summary))
        
        return {
            "messages": messages,
            "saved_path": file_path,
            "saved_filename": filename,
            "file_info": file_info,
            "schedule_file_path": file_path  # 호환성을 위해 유지
        }
        
    except Exception as e:
        logger.error(f"스케줄 파일 저장 실패: {str(e)}")
        
        # 실패시에도 메시지는 업데이트
        messages = state["messages"]
        error_message = f"학습 계획 생성은 완료되었으나 파일 저장에 실패했습니다: {str(e)}"
        messages.append(HumanMessage(content=error_message))
        
        return {
            "messages": messages,
            "error": f"파일 저장 실패: {str(e)}"
        }