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
        response = llm.invoke(f"""사용자의 질문 의도를 분석하고 purpose map을 참고하여 eval()을 이용하여 python 문법에 맞게 json형식으로 바로 변환 가능하게 json형식으로 답변해주세요. 
                         출력 예시는 아래와 같습니다.
                         1) input : 운영체제 1편을 요약해주세요. 
                            \noutput : {{
                                question : "운영체제 1편을 요약해달라 함.",
                                purpose : "summary", 
                            }}
                         2) input : 스파르타 때의 정치는 어떤 것들이 있어요?
                            \noutput : {{
                                question : "스파르타 시기의 정치를 물음.",
                                purpose : "qa_system",
                            }}
               질문 : {question}
               purpose map : {purpose_map}""")
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