# app/api/v1/endpoints/pdf_agent.py

"""
PDF Agent API 라우터

- 기존 RQ 기반 비동기 작업 큐를 제거하고 LangGraph 기반 흐름으로 전환함
- 문서 처리, 요약, 질문 생성, 질의응답 등의 작업을 LangGraph 내에서 상태 기반으로 처리
- 이 파일은 향후 LangGraph 흐름을 직접 호출하여 결과를 반환하는 REST API로 구성됨
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Dict, Any

from app.api import deps
from app.models.user import User
from app.models.tag import PDFFile
from app.core.config import settings

# 각 기능별 LangGraph 빌더 및 상태 초기화 유틸
from app.services.pdf_agent.tools import get_initial_state
from app.services.pdf_agent.graphs.main import intergrate_graph
from app.services.pdf_agent.graphs.qa_graph import get_qa_graph
from app.services.pdf_agent.graphs.summary_graph import get_summary_graph
from app.services.pdf_agent.graphs.exam_graph import get_exam_graph

router = APIRouter()


@router.post("/{document_id}/process", response_model=Dict[str, Any])
async def process_document(
    document_id: int = Path(..., title="PDF 문서 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """LangGraph 기반 PDF 문서 처리 (전처리 + 벡터 저장 등 포함)"""
    from app.services.pdf_agent.tools import get_initial_state
    from app.services.pdf_agent.graphs.main import intergrate_graph

    # 권한 검증
    document = db.query(PDFFile).filter(PDFFile.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
    if not document.team_id and document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")
    if document.team_id:
        from app.services.team_service import check_team_permission
        has_access = await check_team_permission(db=db, team_id=document.team_id, user_id=current_user.id)
        if not has_access:
            raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")

    try:
        # LangGraph 실행
        graph = intergrate_graph()
        state = get_initial_state(folder=document.folder_name, user_id=str(current_user.id))
        result_state = graph.invoke(state)

        return {
            "success": True,
            "document_id": document.id,
            "document_name": document.filename,
            "result": result_state.get("result", ""),
            "message": "LangGraph 기반 문서 처리가 완료되었습니다."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LangGraph 처리 중 오류 발생: {str(e)}")

@router.post("/{document_id}/query", response_model=Dict[str, Any])
async def query_document(
    document_id: int = Path(..., title="PDF 문서 ID"),
    query: str = Body(..., description="질문 내용"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """LangGraph 기반 문서 질의응답 처리"""
    from app.services.pdf_agent.tools import get_initial_state
    from app.services.pdf_agent.graphs.qa_graph import get_qa_graph

    document = db.query(PDFFile).filter(PDFFile.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
    if not document.team_id and document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")
    if document.team_id:
        from app.services.team_service import check_team_permission
        has_access = await check_team_permission(db=db, team_id=document.team_id, user_id=current_user.id)
        if not has_access:
            raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")

    try:
        graph = get_qa_graph()
        state = get_initial_state(folder=document.folder_name, user_id=str(current_user.id))
        state["purpose"] = "qa"
        state["query"] = query

        result_state = graph.invoke(state)

        return {
            "success": True,
            "document_id": document.id,
            "document_name": document.filename,
            "query": query,
            "answer": result_state.get("result", "답변 생성 실패"),
            "message": "LangGraph 기반 질의응답이 완료되었습니다."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"질문 처리 중 오류 발생: {str(e)}")

@router.post("/{document_id}/summarize", response_model=Dict[str, Any])
async def summarize_document(
    document_id: int = Path(..., title="PDF 문서 ID"),
    level: str = Query("default", description="요약 수준 (default, short, detailed)"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """LangGraph 기반 문서 요약 실행"""
    from app.services.pdf_agent.tools import get_initial_state
    from app.services.pdf_agent.graphs.summary_graph import get_summary_graph

    document = db.query(PDFFile).filter(PDFFile.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
    if not document.team_id and document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")
    if document.team_id:
        from app.services.team_service import check_team_permission
        has_access = await check_team_permission(db=db, team_id=document.team_id, user_id=current_user.id)
        if not has_access:
            raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")

    try:
        # 요약용 LangGraph 실행
        graph = get_summary_graph()
        state = get_initial_state(folder=document.folder_name, user_id=str(current_user.id))
        state["purpose"] = "summarize"
        state["summary_level"] = level  # 요약 수준이 필요하다면 상태에 삽입

        result_state = graph.invoke(state)

        return {
            "success": True,
            "document_id": document.id,
            "document_name": document.filename,
            "level": level,
            "summary": result_state.get("result", ""),
            "message": "LangGraph 기반 요약이 완료되었습니다."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요약 처리 중 오류 발생: {str(e)}")

@router.post("/{document_id}/questions", response_model=Dict[str, Any])
async def generate_questions(
    document_id: int = Path(..., title="PDF 문서 ID"),
    count: int = Query(5, description="생성할 문제 수", ge=1, le=20),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """LangGraph 기반 문서 문제 생성"""
    from app.services.pdf_agent.tools import get_initial_state
    from app.services.pdf_agent.graphs.exam_graph import get_exam_graph

    document = db.query(PDFFile).filter(PDFFile.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
    if not document.team_id and document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")
    if document.team_id:
        from app.services.team_service import check_team_permission
        has_access = await check_team_permission(db=db, team_id=document.team_id, user_id=current_user.id)
        if not has_access:
            raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")

    try:
        # 시험 생성용 LangGraph 실행
        graph = get_exam_graph()
        state = get_initial_state(folder=document.folder_name, user_id=str(current_user.id))
        state["purpose"] = "generate_questions"
        state["question_count"] = count

        result_state = graph.invoke(state)

        return {
            "success": True,
            "document_id": document.id,
            "document_name": document.filename,
            "count": count,
            "questions": result_state.get("result", ""),
            "message": "LangGraph 기반 문제 생성이 완료되었습니다."
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문제 생성 중 오류 발생: {str(e)}")