# app/api/v1/endpoints/pdf_agent.py

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging

from app.api import deps
from app.models.user import User
from app.models.tag import PDFFile
from app.services.pdf_agent.tools import get_initial_state
from app.services.pdf_agent.graphs.main import get_processing_graph
from app.services.pdf_agent.graphs.qa_graph import get_qa_graph
from app.services.pdf_agent.graphs.summary_graph import get_summary_graph
from app.services.pdf_agent.graphs.exam_graph import get_exam_graph

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/{document_id}/process", response_model=Dict[str, Any])
async def process_document(
    document_id: int = Path(..., title="PDF 문서 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """LangGraph 기반 PDF 문서 처리 (전처리 + 벡터 저장 등 포함)"""
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
        # document_id를 정수형으로 명시적 변환하여 전달
        state = get_initial_state(
            user_id=str(current_user.id),
            document_id=int(document_id),  # 명시적으로 int 타입 지정
            pdf_path=document.file_path,
            purpose="preprocessing"
        )
        # 디버깅 로그 추가
        logger.info(f"PDF 처리 시작: document_id={document_id}, 상태={state}")

        graph = get_processing_graph()
        result = graph.invoke(state)

        # 결과에 오류가 있으면 HTTPException 발생
        if result.get("error"):
            logger.error(f"PDF 처리 실패: {result.get('error')}")
            raise HTTPException(
                status_code=500, 
                detail=f"문서 처리 중 오류 발생: {result.get('error')}"
            )


        return {
            "success": True,
            "document_id": document.id,
            "document_name": document.filename,
            "message": "문서 처리가 완료되었습니다.",
            "embedding_stored": result.get("embedding_stored", False),
            "error": result.get("error")
        }

    except Exception as e:
        logger.error(f"PDF Agent 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"문서 처리 중 오류 발생: {str(e)}")


@router.post("/{document_id}/query", response_model=Dict[str, Any])
async def query_document(
    document_id: int = Path(..., title="PDF 문서 ID"),
    query: str = Body(..., description="질문 내용"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
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
        state = get_initial_state(
            user_id=str(current_user.id),
            document_id=document_id,
            pdf_path=document.file_path,
            purpose="qa_system",
            query=query
        )
        graph = get_qa_graph()
        result = graph.invoke(state)

        answer = result.get("last_assistant_response", "응답을 생성하지 못했습니다.")

        return {
            "success": True,
            "document_id": document_id,
            "document_name": document.filename,
            "query": query,
            "answer": answer
        }

    except Exception as e:
        logger.error(f"질의응답 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"질문 처리 중 오류 발생: {str(e)}")


@router.post("/{document_id}/summarize", response_model=Dict[str, Any])
async def summarize_document(
    document_id: int = Path(..., title="PDF 문서 ID"),
    level: str = Query("default", description="요약 수준 (default, short, detailed)"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
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
        query_str = f"이 문서를 {level} 수준으로 요약해주세요"
        state = get_initial_state(
            user_id=str(current_user.id),
            document_id=document_id,
            pdf_path=document.file_path,
            purpose="summary",
            query=query_str
        )
        state["summary_level"] = level

        graph = get_summary_graph()
        result = graph.invoke(state)

        summary = result.get("result", "") or result.get("last_assistant_response", "요약을 생성하지 못했습니다.")

        return {
            "success": True,
            "document_id": document_id,
            "document_name": document.filename,
            "level": level,
            "summary": summary
        }

    except Exception as e:
        logger.error(f"요약 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"요약 처리 중 오류 발생: {str(e)}")


@router.post("/{document_id}/questions", response_model=Dict[str, Any])
async def generate_questions(
    document_id: int = Path(..., title="PDF 문서 ID"),
    count: int = Query(5, description="생성할 문제 수", ge=1, le=20),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
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
        query_str = f"이 문서에서 {count}개의 시험 문제를 만들어주세요"
        state = get_initial_state(
            user_id=str(current_user.id),
            document_id=document_id,
            pdf_path=document.file_path,
            purpose="generate_exam",
            query=query_str
        )
        state["question_count"] = count

        graph = get_exam_graph()
        result = graph.invoke(state)

        questions = result.get("result", "") or result.get("last_assistant_response", "문제를 생성하지 못했습니다.")

        return {
            "success": True,
            "document_id": document_id,
            "document_name": document.filename,
            "count": count,
            "questions": questions
        }

    except Exception as e:
        logger.error(f"문제 생성 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"문제 생성 중 오류 발생: {str(e)}")
