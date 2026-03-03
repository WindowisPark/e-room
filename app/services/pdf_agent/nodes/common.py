# app/services/pdf_agent/nodes/common.py

from typing import Dict, Any
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.prompts.common import (
    JUDGE_PURPOSE_PROMPT,
    EXTRACT_TARGET_PROMPT,
)
from app.core.config import settings
import json
import logging
import os

logger = logging.getLogger(__name__)
llm = ChatGoogleGenerativeAI(
    model=settings.AI_MODEL_NAME,
    google_api_key=settings.GOOGLE_API_KEY,
    request_timeout=settings.AI_LLM_TIMEOUT,
)

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
    purpose_map = {
        "summary":{
            "question_example": "사용자가 정확하게 '요약' 이란 단어를 명시하며 요약을 요청,어떠한 문서를 요약해주어야 한다.",
            "purpose" : "summary", 
            } ,
        "qa_system":{
            "question_example": "어떠한 질문에 대한 답변을 해주어야 한다.",
            "purpose" : "qa_system", 
            } ,
        "generate_exam":{
            "question_example": "시험 문제를 생성해주어야 한다.",
            "purpose" : "generate_exam", 
            } ,
        "schedule":{
            "question_example": "학습 계획을 세워주어야 한다.",
            "purpose" : "schedule", 
            } ,
    }

    try:
        response = llm.invoke(JUDGE_PURPOSE_PROMPT.format(question=question, purpose_map=purpose_map))
        content = response.content.strip()

        if content.startswith("```"):
            content = content.strip("`").strip()
        if content.lower().startswith("json"):
            content = content[4:].strip()

        parsed = json.loads(content)
        return {
            "purpose": parsed["purpose"],
        }

    except Exception as e:
        logger.error(f"목적 판단 실패: {str(e)}")
        return {
            "purpose": "qa_system",
        }

def extract_target_file_from_question(state: AgentState) -> Dict[str, Any]:
    """
    스케줄 질문일 경우, 학습 대상 파일 또는 폴더를 추출
    """
    question = state["messages"][-1].content

    try:
        response = llm.invoke(EXTRACT_TARGET_PROMPT.format(question=question))
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