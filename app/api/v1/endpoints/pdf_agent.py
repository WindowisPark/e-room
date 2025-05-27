# app/api/v1/endpoints/pdf_agent.py

# 🚫 이 라우터는 현재 사용되지 않으므로 비활성화 처리 (2025-05-27 기준)
raise ImportError("pdf_agent router is temporarily disabled")

# 아래 코드는 추후 다시 사용할 경우 주석 해제
"""
from fastapi import APIRouter, Body, HTTPException, Depends
from typing import Dict, Any
import logging

from app.models.user import User
from app.api import deps
from app.services.pdf_agent.graphs.main import intergrate_graph
from app.services.pdf_agent.tools import get_initial_state
from app.services.pdf_agent.nodes.common import (
    input_question_api,
    judge_the_purpose_of_the_input,
    extract_target_file_from_question
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/ask", summary="사용자 질문 처리 및 목적에 따른 Graph 실행")
async def ask_question(
    query: str = Body(..., description="사용자의 자연어 질문"),
    user_id: int = Body(..., description="사용자 ID"),
    current_user: User = Depends(deps.get_current_user)
) -> Dict[str, Any]:
    try:
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="다른 사용자의 질문을 처리할 수 없습니다.")

        # 🛠 get_initial_state는 필수 인자 4개 필요 → 임시값 세팅 후 목적에 따라 갱신됨
        state = get_initial_state(
            user_id=str(user_id),
            document_id=0,
            pdf_path="",
            purpose="qa_system",  # 초기 목적, 이후 LLM 판단으로 변경됨
            query=query
        )

        state = input_question_api(state, query)
        state = judge_the_purpose_of_the_input(state)

        if state["purpose"] == "schedule":
            state = extract_target_file_from_question(state)
        else:
            state = select_folder(state)

        graph = intergrate_graph()
        result = graph.invoke(state)

        return {
            "success": True,
            "query": query,
            "purpose": state.get("purpose"),
            "folder": state.get("folder"),
            "answer": result.get("result") or result.get("last_assistant_response") or "응답을 생성하지 못했습니다."
        }

    except Exception as e:
        logger.error(f"/ask 처리 중 오류: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"질문 처리 중 오류 발생: {str(e)}",
            "query": query
        }
"""
