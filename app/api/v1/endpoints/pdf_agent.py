# app/api/v1/endpoints/pdf_agent.py

from app.models.task import Task
from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from app.api import deps
from app.models.user import User
from app.models.tag import PDFFile
from app.services.pdf_agent.embedding_service import EmbeddingService
from app.workers.task_manager import TaskManager
from app.core.config import settings

# 🔁 비동기 처리를 위한 워커 래퍼 함수들
from app.workers.worker import (
    wrapper_process_and_embed_document,
    wrapper_summarize_document,
    wrapper_generate_questions
)

router = APIRouter()
task_manager = TaskManager()

# app/api/v1/endpoints/pdf_agent.py에서 문서 처리 요청 엔드포인트 수정

@router.post("/{document_id}/process", response_model=Dict[str, Any])
async def process_document(
    document_id: int = Path(..., title="PDF 문서 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """PDF 문서 처리 및 임베딩 생성 요청 (비동기 처리)"""
    try:
        # 문서 접근 권한 확인
        document = db.query(PDFFile).filter(PDFFile.id == document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
        
        # 개인 문서이면서 소유자가 아닌 경우 접근 거부
        if not document.team_id and document.owner_id != current_user.id:
            raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")
        
        # 팀 문서인 경우 팀 멤버인지 확인
        if document.team_id:
            from app.services.team_service import check_team_permission
            
            has_access = await check_team_permission(
                db=db,
                team_id=document.team_id,
                user_id=current_user.id
            )
            if not has_access:
                raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")
        
        # 중복 작업 확인
        job_id = f"process_{document_id}_{current_user.id}"
        existing_task = None
        
        try:
            # 트랜잭션 롤백 필요 시 대비
            existing_task = db.query(Task).filter(Task.job_id == job_id).first()
        except:
            db.rollback()
            # 롤백 후 다시 시도
            existing_task = db.query(Task).filter(Task.job_id == job_id).first()
        
        # 이미 존재하는 작업인 경우 처리
        if existing_task:
            # RQ에서 작업 상태 조회
            job_status = task_manager.get_job_status(job_id)
            status = job_status.get("status", "unknown")
            
            # 이미 처리 중 또는 대기 중인 작업
            if status in ["queued", "started"]:
                return {
                    "success": True,
                    "job_id": job_id,
                    "document_id": document_id,
                    "document_name": document.filename,
                    "status": status,
                    "message": f"문서 처리 작업이 이미 {status} 상태입니다. WebSocket을 통해 진행 상황을 확인할 수 있습니다."
                }
        
        # 작업 큐에 등록 - db 세션은 큐로 전달하지 않음
        job_id = task_manager.enqueue_task(
            wrapper_process_and_embed_document,
            queue_name="pdf",
            job_id=f"process_{document_id}_{current_user.id}",
            job_timeout=1800,
            user_id=current_user.id,  # 사용자 ID 전달
            db=db,  # 작업 기록에만 사용됨
            task_type="process_document",
            document_id=document_id
        )
        
        return {
            "success": True,
            "job_id": job_id,
            "document_id": document_id,
            "document_name": document.filename,
            "status": "pending",
            "message": "문서 처리 작업이 시작되었습니다. WebSocket을 통해 진행 상황을 확인할 수 있습니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"문서 처리 작업 등록 중 오류 발생: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"문서 처리 작업 등록 중 오류 발생: {str(e)}")

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

    # 사용자 ID 전달하도록 수정
    similar_chunks = await PDFAgent.search_similar_chunks(
        db=db, 
        user_id=current_user.id,
        document_id=document_id, 
        query_text=query, 
        limit=5
    )

    if not similar_chunks:
        return {
            "success": True,
            "document_id": document_id,
            "document_name": document.filename,
            "query": query,
            "answer": "이 질문에 대한 답변을 문서에서 찾을 수 없습니다.",
            "contexts": []
        }

    contexts = [chunk["text"] for chunk in similar_chunks]
    answer = await PDFAgent.generate_answer(query, contexts)

    return {
        "success": True,
        "document_id": document_id,
        "document_name": document.filename,
        "query": query,
        "answer": answer,
        "contexts": similar_chunks
    }

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

    job_id = task_manager.enqueue_task(
        wrapper_summarize_document,
        document_id,
        level,
        queue_name="ai",
        job_id=f"summarize_{document_id}_{current_user.id}",
        job_timeout=1800,
        user_id=current_user.id,
        task_type="summarize",
        document_id=document_id
    )

    return {
        "success": True,
        "job_id": job_id,
        "document_id": document_id,
        "document_name": document.filename,
        "level": level,
        "status": "pending",
        "message": "요약 작업이 시작되었습니다. WebSocket을 통해 진행 상황을 확인할 수 있습니다."
    }

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

    job_id = task_manager.enqueue_task(
        wrapper_generate_questions,
        document_id,
        count,
        queue_name="ai",
        job_id=f"questions_{document_id}_{current_user.id}",
        job_timeout=1800,
        user_id=current_user.id,
        task_type="generate_questions",
        document_id=document_id
    )

    return {
        "success": True,
        "job_id": job_id,
        "document_id": document_id,
        "document_name": document.filename,
        "count": count,
        "status": "pending",
        "message": "문제 생성 작업이 시작되었습니다. WebSocket을 통해 진행 상황을 확인할 수 있습니다."
    }


# 작업 상태 조회 엔드포인트
@router.get("/tasks/{job_id}", response_model=Dict[str, Any])
async def get_task_status(
    job_id: str = Path(..., title="작업 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """작업 상태 조회"""
    try:
        # 작업 상태 조회
        job_status = task_manager.get_job_status(job_id)
        
        # 소유자 확인 (작업 ID에 사용자 ID가 포함된 경우)
        if job_id.endswith(f"_{current_user.id}"):
            return {
                "success": True,
                "job_id": job_id,
                "status": job_status.get("status", "unknown"),
                "progress": job_status.get("progress", 0),
                "result": job_status.get("result"),
                "error": job_status.get("error"),
                "message": job_status.get("message", "작업 상태 조회 성공")
            }
        else:
            # DB에서 작업 소유자 확인
            from app.crud.crud_task import get_task_by_job_id
            
            task = get_task_by_job_id(db, job_id)
            if task and task.user_id == current_user.id:
                return {
                    "success": True,
                    "job_id": job_id,
                    "status": job_status.get("status", "unknown"),
                    "progress": job_status.get("progress", 0),
                    "result": job_status.get("result"),
                    "error": job_status.get("error"),
                    "message": job_status.get("message", "작업 상태 조회 성공")
                }
            else:
                raise HTTPException(status_code=403, detail="해당 작업에 접근할 권한이 없습니다")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"작업 상태 조회 중 오류 발생: {str(e)}")

# 작업 취소 엔드포인트
@router.delete("/tasks/{job_id}", response_model=Dict[str, Any])
async def cancel_task(
    job_id: str = Path(..., title="작업 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """작업 취소"""
    try:
        # 소유자 확인
        if not job_id.endswith(f"_{current_user.id}"):
            # DB에서 작업 소유자 확인
            from app.crud.crud_task import get_task_by_job_id
            
            task = get_task_by_job_id(db, job_id)
            if not task or task.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="해당 작업을 취소할 권한이 없습니다")
        
        # 작업 취소
        success = task_manager.cancel_job(job_id)
        
        if success:
            return {
                "success": True,
                "job_id": job_id,
                "message": "작업이 취소되었습니다"
            }
        else:
            return {
                "success": False,
                "job_id": job_id,
                "message": "작업 취소에 실패했습니다. 이미 완료되었거나 찾을 수 없는 작업일 수 있습니다."
            }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"작업 취소 중 오류 발생: {str(e)}")

# 사용자 작업 목록 조회 엔드포인트
@router.get("/tasks", response_model=List[Dict[str, Any]])
async def list_user_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None, description="작업 상태 필터 (queued, started, finished, failed)"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """사용자의 작업 목록 조회"""
    try:
        from app.crud.crud_task import get_tasks_by_user
        
        # DB에서 사용자 작업 목록 조회
        tasks = get_tasks_by_user(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
        
        # 작업 상세 정보 추가
        result = []
        for task in tasks:
            # 작업 상태 조회
            job_status = task_manager.get_job_status(task.job_id)
            
            result.append({
                "id": task.id,
                "job_id": task.job_id,
                "task_type": task.task_type,
                "document_id": task.document_id,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "updated_at": task.updated_at.isoformat() if task.updated_at else None,
                "status": job_status.get("status", task.status),
                "progress": job_status.get("progress", 0),
                "result": task.result
            })
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"작업 목록 조회 중 오류 발생: {str(e)}")