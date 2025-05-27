# app/services/pdf_agent/nodes/qa_system.py (완전 수정 버전)

import logging
import os
from typing import Dict, Any
from dotenv import dotenv_values
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

# ✅ 필수 임포트 추가
from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.tools import search_documents_for_qa

# 환경 변수 및 LLM 설정
envs = dotenv_values(".env")
api_key = envs.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY", ""))

# LLM 초기화
if api_key:
    llm = ChatOpenAI(model="gpt-4o-mini", api_key=api_key)
else:
    # API 키가 없을 때 대체 처리
    llm = None

logger = logging.getLogger(__name__)

def start_point_of_qa_system(state: AgentState) -> Dict[str, Any]:
    """
    QA 시스템 진입점
    WebSocket 환경에 맞게 수정된 버전
    """
    try:
        messages = state.get("messages", [])
        if not messages:
            return {
                "messages": messages, 
                "last_assistant_response": "질문을 입력해주세요."
            }

        # 마지막 사용자 메시지 가져오기
        user_input = ""
        for message in reversed(messages):
            if hasattr(message, 'content') and hasattr(message, '__class__'):
                if "HumanMessage" in str(message.__class__):
                    user_input = message.content
                    break
        
        if not user_input:
            return {
                "messages": messages,
                "last_assistant_response": "유효한 질문을 찾을 수 없습니다."
            }

        logger.info(f"QA 처리 시작: {user_input[:50]}...")

        # LLM이 초기화되지 않은 경우 처리
        if llm is None:
            error_response = "OpenAI API 키가 설정되지 않았습니다. 관리자에게 문의하세요."
            messages.append(AIMessage(content=error_response))
            return {
                "messages": messages,
                "last_assistant_response": error_response
            }

        # 자료 참조 필요 여부 판단
        check_prompt = f"""다음 질문이 자료 참조가 필요한지(전문적인 고난이도 질문), 
        기본적인 내재 지식으로 답변 가능(간단하거나 낮은 난이도의 질문)한지 판단하여 숫자만 답변해주세요.
        자료 참조 필요(1), 내재 지식으로 답변 가능(0)
        질문: {user_input}"""
        
        try:
            check_response = llm.invoke(check_prompt)
            check = check_response.content.strip()
            
            if check == "1":
                logger.info("[자료 참조 필요]")
                # ChromaDB에서 관련 문서 검색
                user_id = state.get("user_id", "")
                if user_id:
                    search_results = search_documents_for_qa(user_id=user_id, query=user_input)
                    
                    # 검색 결과를 텍스트로 변환
                    material_text = ""
                    if search_results:
                        for doc, score in search_results[:3]:  # 상위 3개만 사용
                            material_text += f"관련 자료 (유사도: {score:.2f}):\n{doc.page_content}\n\n"
                    
                    if material_text:
                        request_content = f"""다음 질문에 자료를 참고하여 답변해주세요.
                        만약 자료의 내용으로는 설명이 불가하거나 충분하지 못하다면, 알고있는 지식을 이용하여 보충 설명해주세요.
                        
                        참고 자료:
                        {material_text}
                        
                        질문: {user_input}"""
                    else:
                        request_content = f"""관련 자료를 찾지 못했습니다. 일반적인 지식을 바탕으로 답변해주세요.
                        질문: {user_input}"""
                else:
                    request_content = f"""사용자 정보가 없어 자료 검색이 불가능합니다. 일반적인 지식을 바탕으로 답변해주세요.
                    질문: {user_input}"""
            else:
                logger.info("[자료 참조 불필요]")
                request_content = f"""다음 질문에 친절하고 자세하게 답변해주세요.
                질문: {user_input}"""
            
            # LLM에 요청하여 답변 생성
            response = llm.invoke(request_content)
            result = response.content
            
            # 응답을 메시지에 추가
            messages.append(AIMessage(content=result))
            
            logger.info(f"QA 응답 생성 완료: {result[:50]}...")
            
            return {
                "messages": messages, 
                "last_assistant_response": result
            }
            
        except Exception as llm_error:
            logger.error(f"LLM 처리 중 오류: {str(llm_error)}")
            error_response = f"답변 생성 중 오류가 발생했습니다: {str(llm_error)}"
            messages.append(AIMessage(content=error_response))
            return {
                "messages": messages,
                "last_assistant_response": error_response
            }
            
    except Exception as e:
        logger.error(f"QA 시스템 전체 오류: {str(e)}", exc_info=True)
        error_response = "죄송합니다. 시스템 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
        
        messages = state.get("messages", [])
        messages.append(AIMessage(content=error_response))
        
        return {
            "messages": messages,
            "last_assistant_response": error_response
        }