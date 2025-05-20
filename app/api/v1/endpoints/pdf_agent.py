# app/api/v1/endpoints/pdf_agent.py

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
from langchain_core.messages import HumanMessage

from app.api import deps
from app.models.user import User
from app.models.tag import PDFFile
from app.services.pdf_agent.tools import get_initial_state
from app.services.pdf_agent.graphs.main import intergrate_graph, simple_graph, get_processing_graph
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
    # 1. 문서와 사용자 권한 검증
    document = db.query(PDFFile).filter(PDFFile.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
    
    # 개인 소유 문서 권한 확인
    if not document.team_id and document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")
    
    # 팀 소유 문서 권한 확인
    if document.team_id:
        from app.services.team_service import check_team_permission
        has_access = await check_team_permission(db=db, team_id=document.team_id, user_id=current_user.id)
        if not has_access:
            raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")
    
    try:
        # 2. 단순 그래프 실행으로 테스트
        state = get_initial_state()
        
        # 중요 필드 설정
        state["user_id"] = str(current_user.id)
        state["document_id"] = document_id
        state["folder"] = "default"  # 기본 폴더 설정
        
        # 3. 단순 그래프 실행
        logger.info(f"PDF Agent 단순 그래프 실행 - 문서 ID: {document_id}, 사용자 ID: {current_user.id}")
        graph = get_processing_graph()
        result = graph.invoke(state)
        
        # 4. 결과 반환
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
    """LangGraph 기반 문서 질의응답"""
    # 1. 문서 및 권한 검증
    document = db.query(PDFFile).filter(PDFFile.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
    
    # 권한 검증
    if not document.team_id and document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")
    
    if document.team_id:
        from app.services.team_service import check_team_permission
        has_access = await check_team_permission(db=db, team_id=document.team_id, user_id=current_user.id)
        if not has_access:
            raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")
    
    try:
        # 2. LangGraph 상태 초기화 및 실행
        state = get_initial_state()
        state["user_id"] = str(current_user.id)
        state["document_id"] = document_id
        state["folder"] = "default"
        state["purpose"] = "qa_system"
        state["last_user_query"] = query  # 메시지 대신 직접 쿼리 설정
        
        # 3. QA 그래프 실행
        graph = get_qa_graph()
        result = graph.invoke(state)
        
        # 4. 결과 추출 및 반환
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
    """LangGraph 기반 문서 요약"""
    # 1. 문서 및 권한 검증
    document = db.query(PDFFile).filter(PDFFile.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
    
    # 권한 검증
    if not document.team_id and document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")
    
    if document.team_id:
        from app.services.team_service import check_team_permission
        has_access = await check_team_permission(db=db, team_id=document.team_id, user_id=current_user.id)
        if not has_access:
            raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")
    
    try:
        # 2. 요약 그래프 실행
        state = get_initial_state()
        state["user_id"] = str(current_user.id)
        state["document_id"] = document_id
        state["folder"] = "default"
        state["purpose"] = "summary"
        state["summary_level"] = level
        state["last_user_query"] = f"이 문서를 {level} 수준으로 요약해주세요"
        
        # 3. 요약 그래프 실행
        graph = get_summary_graph()
        result = graph.invoke(state)
        
        # 4. 결과 추출 및 반환
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
    """LangGraph 기반 문서 문제 생성"""
    # 1. 문서 및 권한 검증
    document = db.query(PDFFile).filter(PDFFile.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
    
    # 권한 검증
    if not document.team_id and document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")
    
    if document.team_id:
        from app.services.team_service import check_team_permission
        has_access = await check_team_permission(db=db, team_id=document.team_id, user_id=current_user.id)
        if not has_access:
            raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")
    
    try:
        # 2. 문제 생성 그래프 실행
        state = get_initial_state()
        state["user_id"] = str(current_user.id)
        state["document_id"] = document_id
        state["folder"] = "default"
        state["purpose"] = "generate_exam"
        state["question_count"] = count
        state["last_user_query"] = f"이 문서에서 {count}개의 시험 문제를 만들어주세요"
        
        # 3. 문제 생성 그래프 실행
        graph = get_exam_graph()
        result = graph.invoke(state)
        
        # 4. 결과 추출 및 반환
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