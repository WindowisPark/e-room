# app/services/pdf_agent/nodes/common.py

from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, BaseMessage
from langchain_openai import ChatOpenAI
from app.services.pdf_agent.states import AgentState, MessageAnnotation
import os
import logging
import re

# 로깅 설정
logger = logging.getLogger(__name__)

# 환경변수에서 API 키 로드
API_KEY = os.getenv("OPENAI_API_KEY", "")

# LLM 초기화
try:
    llm = ChatOpenAI(model="gpt-3.5-turbo", api_key=API_KEY)
except Exception as e:
    logger.error(f"LLM 초기화 오류: {str(e)}")
    llm = None


def input_question(state: AgentState) -> Dict[str, Any]:
    """
    사용자 질문을 확인하고 필요시 기본 질문 추가
    
    Args:
        state: LangGraph 상태 객체
        
    Returns:
        업데이트된 상태 객체
    """
    # 새로운 메시지 목록 생성 (복사가 아님)
    messages = list(state.get("messages", []))
    
    # 시스템 메시지가 없으면 추가
    if not messages or not any(isinstance(msg, SystemMessage) for msg in messages):
        system_message = SystemMessage(content="""당신은 PDF 문서를 분석하고 이해하는 AI 어시스턴트입니다. 
        문서에 대한 요약, 질문 답변, 시험 문제 생성 등의 작업을 수행할 수 있습니다.""")
        messages.insert(0, system_message)
    
    # 사용자 메시지가 없으면 기본 질문 추가
    if not any(isinstance(msg, HumanMessage) for msg in messages):
        default_question = "문서를 요약해주세요."
        messages.append(HumanMessage(content=default_question))
        
        # 마지막 질문도 업데이트
        last_user_query = default_question
    else:
        # 마지막 사용자 메시지 추출
        user_messages = [msg for msg in messages if isinstance(msg, HumanMessage)]
        last_user_query = user_messages[-1].content if user_messages else ""
    
    # 반환 - 새로운 상태 객체 생성
    return {
        **state,
        "messages": messages,
        "last_user_query": last_user_query
    }


def process_user_input(state: AgentState) -> Dict[str, Any]:
    """
    사용자 입력을 처리하고 상태 업데이트
    이 함수는 messages 키 대신 last_user_query를 사용
    """
    query = state.get("last_user_query", "")
    
    if not query:
        # 메시지에서 쿼리 추출 시도
        messages = state.get("messages", [])
        user_messages = [msg for msg in messages if isinstance(msg, HumanMessage)]
        query = user_messages[-1].content if user_messages else "문서를 요약해주세요."
    
    # AI 응답 생성
    if llm and query:
        try:
            response = llm.invoke(query)
            assistant_response = response.content
        except Exception as e:
            logger.error(f"응답 생성 오류: {str(e)}")
            assistant_response = "처리 중 오류가 발생했습니다."
    else:
        assistant_response = "LLM이 초기화되지 않았거나 쿼리가 비어 있습니다."
    
    # 상태 업데이트
    return {
        **state,
        "last_assistant_response": assistant_response
    }


def judge_the_purpose_of_the_input(state: AgentState) -> Dict[str, Any]:
    """
    사용자 입력의 목적을 식별 (요약, 질문응답, 시험문제 생성 등)
    - messages 키 대신 last_user_query 사용
    """
    if not llm:
        return {**state, "purpose": "summary", "error": "LLM 초기화 실패로 기본 목적(요약)을 사용합니다."}
    
    try:
        # last_user_query 사용
        query = state.get("last_user_query", "")
        
        if not query:
            # 메시지에서 쿼리 추출 시도
            messages = state.get("messages", [])
            user_messages = [msg for msg in messages if isinstance(msg, HumanMessage)]
            query = user_messages[-1].content if user_messages else ""
            
        if not query:
            return {**state, "purpose": "summary"}
        
        # 요약 키워드 직접 검사 (한국어 자연어 처리 보완)
        if any(keyword in query for keyword in ["요약", "정리", "간추려", "축약", "핵심"]):
            return {**state, "purpose": "summary"}
        
        # 목적 분류를 위한 프롬프트
        prompt = f"""
        다음 사용자 메시지의 목적을 분석해 주세요.
        
        사용자 메시지: "{query}"
        
        가능한 목적:
        1. summary - 문서를 요약해달라는 요청
        2. qa_system - 문서에 대한 질문에 답변해달라는 요청
        3. generate_exam - 문서 기반 시험 문제 생성 요청
        4. schedule - 학습 계획 생성 요청
        
        응답은 다음 형식 중 하나로만 정확히 응답해 주세요: "summary", "qa_system", "generate_exam", "schedule"
        """
        
        # 분류 수행
        response = llm.invoke(prompt)
        purpose = response.content.strip().lower()
        
        # 유효한 목적 확인
        valid_purposes = ["summary", "qa_system", "generate_exam", "schedule"]
        if purpose not in valid_purposes:
            logger.warning(f"인식된 목적이 유효하지 않음: {purpose}, 기본값 사용")
            purpose = "summary"
        
        return {**state, "purpose": purpose}
        
    except Exception as e:
        logger.error(f"목적 판단 중 오류: {str(e)}")
        return {**state, "purpose": "summary", "error": f"목적 판단 실패: {str(e)}"}


def router(state: AgentState) -> str:
    """
    다음 단계를 결정하는 라우터 함수
    """
    purpose = state.get("purpose", "")
    
    if purpose == "summary":
        return "summary"
    elif purpose == "qa_system":
        return "qa_system"
    elif purpose == "generate_exam":
        return "generate_exam"
    elif purpose == "schedule":
        return "schedule"
    else:
        return "summary"  # 기본값


def select_folder(state: AgentState) -> Dict[str, Any]:
    """
    폴더 선택 - messages 키 대신 last_user_query 사용
    """
    # 이미 폴더가 지정되어 있으면 그대로 사용
    if state.get("folder"):
        return state
        
    try:
        user_id = state.get("user_id", "default")
        base_path = f"storage/users/{user_id}"
        
        # 사용자 폴더가 존재하는지 확인
        if not os.path.exists(base_path):
            return {**state, "folder": "default"}
            
        # 사용자 폴더 목록 가져오기
        folders = [f for f in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, f))]
        
        if not folders:
            return {**state, "folder": "default"}
            
        # 쿼리가 있는 경우 LLM을 사용하여 적절한 폴더 선택
        query = state.get("last_user_query", "")
        
        if not query or not llm:
            return {**state, "folder": folders[0]}  # 첫 번째 폴더 선택
            
        prompt = f"""
        다음 사용자 메시지에 가장 관련 있는 폴더를 선택해 주세요:
        
        사용자 메시지: "{query}"
        
        가능한 폴더 목록: {folders}
        
        응답은 목록에 있는 폴더 이름 하나만 정확히 입력해 주세요.
        """
        
        response = llm.invoke(prompt)
        selected_folder = response.content.strip()
        
        # 선택된 폴더가 실제 존재하는지 확인
        if selected_folder in folders:
            return {**state, "folder": selected_folder}
        else:
            # 존재하지 않으면 첫 번째 폴더 사용
            logger.warning(f"선택된 폴더 '{selected_folder}'가 존재하지 않아 첫 번째 폴더 '{folders[0]}'를 사용")
            return {**state, "folder": folders[0]}
            
    except Exception as e:
        logger.error(f"폴더 선택 중 오류: {str(e)}")
        return {**state, "folder": "default", "error": f"폴더 선택 실패: {str(e)}"}