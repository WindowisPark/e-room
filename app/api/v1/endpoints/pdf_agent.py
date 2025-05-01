from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Path
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from app.api import deps
from app.models.user import User
from app.models.tag import PDFFile
from app.services.pdf_agent.ai_agent import PDFAgent
from app.workers.task_manager import TaskManager
from app.core.config import settings

router = APIRouter()
task_manager = TaskManager()

# PDF 문서 목록 조회
@router.get("/documents", response_model=List[Dict[str, Any]])
async def get_user_documents(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """사용자의 PDF 문서 목록 조회"""
    try:
        # 사용자의 PDF 파일 조회
        pdf_files = (
            db.query(PDFFile)
            .filter(PDFFile.owner_id == current_user.id)
            .offset(skip)
            .limit(limit)
            .all()
        )
        
        # 응답 데이터 구성
        documents = []
        for pdf in pdf_files:
            documents.append({
                "id": pdf.id,
                "filename": pdf.filename,
                "file_path": pdf.file_path,
                "created_at": pdf.created_at.isoformat() if pdf.created_at else None,
                "team_id": pdf.team_id
            })
        
        return documents
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문서 목록 조회 중 오류 발생: {str(e)}")

# 문서 요약 요청
@router.post("/{document_id}/summarize", response_model=Dict[str, Any])
async def summarize_document(
    document_id: int = Path(..., title="PDF 문서 ID"),
    level: str = Query("default", description="요약 수준 (default, short, detailed)"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """PDF 문서 요약 요청 (비동기 처리)"""
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
            has_access = check_team_permission(
                db=db,
                team_id=document.team_id,
                user_id=current_user.id
            )
            if not has_access:
                raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")
        
        # 작업 큐에 등록
        job_id = task_manager.enqueue_task(
            PDFAgent.summarize,
            db,
            document_id,
            level,
            queue_name="ai",
            job_id=f"summarize_{document_id}_{current_user.id}"
        )
        
        # 작업 상태 DB에 기록
        task_record = create_task_record(
            db,
            user_id=current_user.id,
            task_type="summarize",
            document_id=document_id,
            job_id=job_id
        )
        
        return {
            "task_id": task_record.id,
            "job_id": job_id,
            "document_id": document_id,
            "document_name": document.filename,
            "level": level,
            "status": "pending",
            "message": "요약 작업이 시작되었습니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요약 작업 등록 중 오류 발생: {str(e)}")

# 문제 생성 요청
@router.post("/{document_id}/questions", response_model=Dict[str, Any])
async def generate_questions(
    document_id: int = Path(..., title="PDF 문서 ID"),
    count: int = Query(5, description="생성할 문제 수", ge=1, le=20),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """PDF 문서 기반 문제 생성 요청 (비동기 처리)"""
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
            has_access = check_team_permission(
                db=db,
                team_id=document.team_id,
                user_id=current_user.id
            )
            if not has_access:
                raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")
        
        # 작업 큐에 등록
        job_id = task_manager.enqueue_task(
            PDFAgent.generate_questions,
            db,
            document_id,
            count,
            queue_name="ai",
            job_id=f"questions_{document_id}_{current_user.id}"
        )
        
        # 작업 상태 DB에 기록 (실제 구현 필요)
        # task_record = create_task_record(
        #    db,
        #    user_id=current_user.id,
        #    task_type="generate_questions",
        #    document_id=document_id,
        #    job_id=job_id
        # )
        
        return {
            "task_id": f"questions_{document_id}_{current_user.id}",
            "job_id": job_id,
            "document_id": document_id,
            "document_name": document.filename,
            "count": count,
            "status": "pending",
            "message": "문제 생성 작업이 시작되었습니다. WebSocket을 통해 진행 상황을 확인할 수 있습니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"문제 생성 작업 등록 중 오류 발생: {str(e)}")

# 질문 답변 요청
@router.post("/{document_id}/answer", response_model=Dict[str, Any])
async def answer_question(
    document_id: int = Path(..., title="PDF 문서 ID"),
    question: str = Query(..., description="질문 내용"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """PDF 문서 기반 질문 답변 요청 (비동기 처리)"""
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
            has_access = check_team_permission(
                db=db,
                team_id=document.team_id,
                user_id=current_user.id
            )
            if not has_access:
                raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")
        
        # 작업 큐에 등록
        job_id = task_manager.enqueue_task(
            PDFAgent.answer_question,
            db,
            document_id,
            question,
            queue_name="ai",
            job_id=f"answer_{document_id}_{current_user.id}"
        )
        
        # 작업 상태 DB에 기록 (실제 구현 필요)
        # task_record = create_task_record(
        #    db,
        #    user_id=current_user.id,
        #    task_type="answer_question",
        #    document_id=document_id,
        #    job_id=job_id
        # )
        
        return {
            "task_id": f"answer_{document_id}_{current_user.id}",
            "job_id": job_id,
            "document_id": document_id,
            "document_name": document.filename,
            "question": question,
            "status": "pending",
            "message": "질문 답변 작업이 시작되었습니다. WebSocket을 통해 진행 상황을 확인할 수 있습니다."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"질문 답변 작업 등록 중 오류 발생: {str(e)}")

# 작업 상태 조회
@router.get("/tasks/{job_id}", response_model=Dict[str, Any])
async def get_task_status(
    job_id: str = Path(..., title="작업 ID"),
    current_user: User = Depends(deps.get_current_user)
):
    """작업 상태 조회"""
    try:
        # 작업 상태 조회
        job_status = task_manager.get_job_status(job_id)
        
        # 소유자 확인 (실제 구현에서는 DB 조회 필요)
        if job_id.endswith(f"_{current_user.id}"):
            return {
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


# 팀 권한 확인 함수 (임시 구현)
def check_team_permission(db: Session, team_id: int, user_id: int) -> bool:
    """팀 접근 권한 확인 (임시 구현)"""
    # 실제 구현에서는 app/services/team_service.py의 check_team_permission 함수 사용
    return True