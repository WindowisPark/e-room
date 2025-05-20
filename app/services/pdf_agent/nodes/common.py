# app/services/pdf_agent/nodes/common.py

from typing import Dict
from dotenv import dotenv_values
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from app.services.pdf_agent.states import AgentState
import os

# 환경변수 로드 및 LLM 초기화
envs = dotenv_values(".env")
api_key = envs.get("OPENAI_API_KEY", "")
llm = ChatOpenAI(model="gpt-3.5-turbo", api_key=api_key)


def input_question(state: AgentState) -> dict:
    """사용자에게 질문을 직접 입력받아 state 업데이트"""
    messages = state.get("messages", [])
    # 이미 메시지가 추가됐으면 그대로 반환
    if len(messages) > 1:  # 시스템 메시지 외에 다른 메시지가 있는지 확인
        return state
    
    # 기본 질문 추가
    default_question = "문서를 처리하고 분석해주세요"
    messages.append(HumanMessage(content=default_question))
    return {**state, "messages": messages}


def judge_the_purpose_of_the_input(state: AgentState) -> dict:
    """
    사용자 입력의 목적을 판단하여 state에 반영
    예: 요약, 질문응답, 시험문제 생성 등
    """
    question = state["messages"][-1].content

    purpose_map = {
        "summary": {
            "question_example": "운영체제 1편을 요약해주세요.",
            "purpose": "summary",
            "full_document": 1,
        },
        "qa_system": {
            "question_example": "스파르타 시기의 정치를 물음.",
            "purpose": "qa_system",
            "full_document": 0,
        },
        "generate_exam": {
            "question_example": "시험 문제를 생성해줘.",
            "purpose": "generate_exam",
            "full_document": 1,
        },
        "schedule": {
            "question_example": "학습 계획을 세워줘.",
            "purpose": "schedule",
            "full_document": 1,
        },
    }

    prompt = f"""
    다음 사용자 질문의 의도를 분석해서 JSON 형식으로 추출해 주세요.
    참고할 수 있는 목적 맵: {purpose_map}

    사용자 질문:
    "{question}"

    출력 형식 예시:
    {{
        "question": "운영체제 1편을 요약해달라 함.",
        "purpose": "summary",
        "full_document": 1
    }}
    """

    try:
        response = llm.invoke(prompt)
        purpose_json = eval(response.content)  # ⚠️ eval 주의 (신뢰된 환경 가정)
        return {
            **state,
            "purpose": purpose_json["purpose"],
            "full_document": purpose_json["full_document"]
        }
    except Exception as e:
        return {**state, "error": f"질문 분석 실패: {str(e)}"}


def router(state: AgentState) -> str:
    """
    LangGraph의 분기점으로 사용되는 라우터
    """
    return state.get("purpose", "unknown")


def select_folder(state: AgentState) -> dict:
    """
    질문과 가장 관련 있는 폴더 선택 (ChromaDB 기반)
    """
    user_id = state["user_id"]
    messages = state["messages"]
    folders_path = f"storage/users/{user_id}/chroma"

    try:
        folders = os.listdir(folders_path)
        question = messages[-1].content

        prompt = f"""
        아래 폴더 목록 중, 다음 질문과 가장 관련된 하나의 폴더 이름만 정확하게 골라주세요.

        질문: "{question}"
        폴더 목록: {folders}
        """

        selected = llm.invoke(prompt).content.strip()

        return {**state, "folder": selected}
    except Exception as e:
        return {**state, "error": f"폴더 선택 실패: {str(e)}"}  
