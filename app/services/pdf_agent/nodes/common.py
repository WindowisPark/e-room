# app/services/pdf_agent/nodes/common.py

from typing import Dict, Any
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI
from app.services.pdf_agent.states import AgentState
import json
import logging
import os

logger = logging.getLogger(__name__)
llm = ChatOpenAI(model="gpt-4.1-nano")

def input_question_api(state: AgentState, query: str) -> Dict[str, Any]:
    """
    API용 사용자 질문 입력 함수
    """
    messages = state["messages"]
    messages.append(HumanMessage(content=query))
    return {**state, "messages": messages}

def judge_the_purpose_of_the_input(state: AgentState) -> Dict[str, Any]:
    """
    사용자 질문의 목적을 LLM을 통해 판단
    (summary / qa_system / generate_exam / schedule)
    """
    question = state["messages"][-1].content
    prompt = f"""
다음 사용자의 질문을 분석하여 목적을 아래 JSON 형식으로 출력하세요:
{{
  "question": "사용자의 질문 요약",
  "purpose": "summary | qa_system | generate_exam | schedule 중 하나",
  "full_document": 1 또는 0
}}

사용자 질문: "{question}"
"""

    try:
        response = llm.invoke(prompt)
        content = response.content.strip()

        if content.startswith("```"):
            content = content.strip("`").strip()
        if content.lower().startswith("json"):
            content = content[4:].strip()

        parsed = json.loads(content)
        return {
            **state,
            "purpose": parsed["purpose"],
            "full_document": parsed["full_document"]
        }

    except Exception as e:
        logger.error(f"목적 판단 실패: {str(e)}")
        return {
            **state,
            "purpose": "qa_system",
            "full_document": 0
        }

def extract_target_file_from_question(state: AgentState) -> Dict[str, Any]:
    """
    스케줄 질문일 경우, 학습 대상 파일 또는 폴더를 추출
    """
    question = state["messages"][-1].content

    prompt = f"""
다음 문장에서 어떤 파일 또는 폴더를 기준으로 학습 계획을 세워야 하는지 판단해주세요.
- 파일명이나 폴더명이 명시되어 있다면 그것을 반환
- 없으면 "None"을 반환
- 형식: {{"target": "정보보호_암호학.pdf"}} 또는 {{"target": "None"}}

질문: "{question}"
"""

    try:
        response = llm.invoke(prompt)
        text = response.content.strip()
        if text.startswith("```"):
            text = text.strip("`").strip()
        if text.lower().startswith("json"):
            text = text[4:].strip()

        result = json.loads(text)
        return {**state, "folder": result.get("target", "None")}

    except Exception as e:
        logger.warning(f"문서 추출 실패: {str(e)}")
        return {**state, "folder": "None"}

def select_folder(state: AgentState) -> Dict[str, Any]:
    """
    LLM이 사용자 질문과 가장 관련 있는 폴더명을 예측하여 상태에 저장
    실제 사용하는 폴더가 명시되지 않은 경우 fallback 용도로 사용됨
    """
    user_id = state["user_id"]
    query = state["messages"][-1].content
    base_path = f"{user_id}/chroma"

    try:
        folders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
        if not folders:
            return {**state, "folder": "None"}

        prompt = f"""
다음 폴더 중 사용자 질문과 가장 관련 있는 폴더명을 하나만 선택하세요.
질문: "{query}"
폴더 목록: {folders}
"""
        response = llm.invoke(prompt)
        selected = response.content.strip()

        if selected not in folders:
            selected = folders[0]

        return {**state, "folder": selected}

    except Exception as e:
        logger.warning(f"폴더 추론 실패: {str(e)}")
        return {**state, "folder": "None"}

def router(state: AgentState) -> str:
    """
    목적에 따라 그래프 라우팅
    """
    return state.get("purpose", "qa_system")

def input_question(state: AgentState) -> Dict[str, Any]:
    """
    LangGraph에서 진입점으로 사용될 수 있도록 input_question_api를 래핑한 함수
    """
    query = state.get("last_user_query", "")
    return input_question_api(state, query)