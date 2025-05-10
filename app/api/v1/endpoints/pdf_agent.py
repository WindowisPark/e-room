# app/api/v1/endpoints/pdf_agent.py의 개선사항

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, List, Optional

from app.api import deps
from app.models.user import User
from app.models.tag import PDFFile
from app.services.pdf_agent.ai_agent import PDFAgent
from app.services.pdf_agent.processor import PDFProcessor
from app.services.pdf_agent.embedding_service import EmbeddingService
from app.workers.task_manager import TaskManager
from app.core.config import settings

router = APIRouter()
task_manager = TaskManager()

# 문서 처리 요청 엔드포인트
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
        
        # 작업 큐에 등록
        job_id = task_manager.enqueue_task(
            PDFProcessor.process_and_embed_document,
            db,
            document_id,
            queue_name="pdf",
            job_id=f"process_{document_id}_{current_user.id}",
            job_timeout=1800,  # 30분 타임아웃
            user_id=current_user.id,
            db=db,
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
        raise HTTPException(status_code=500, detail=f"문서 처리 작업 등록 중 오류 발생: {str(e)}")

# 문서 질의응답 엔드포인트
@router.post("/{document_id}/query", response_model=Dict[str, Any])
async def query_document(
    document_id: int = Path(..., title="PDF 문서 ID"),
    query: str = Body(..., description="질문 내용"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """PDF 문서 기반 질의응답"""
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
        
        # 임베딩 서비스 초기화
        embedding_service = EmbeddingService()
        
        # 유사한 청크 검색 (비동기)
        similar_chunks = await embedding_service.search_similar_chunks_async(
            db=db,
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
        
        # 유사 청크들로 컨텍스트 구성
        contexts = [chunk["text"] for chunk in similar_chunks]
        
        # AI 모델로 답변 생성
        answer = await PDFAgent.generate_answer(query, contexts)
        
        return {
            "success": True,
            "document_id": document_id,
            "document_name": document.filename,
            "query": query,
            "answer": answer,
            "contexts": similar_chunks
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"질의응답 중 오류 발생: {str(e)}")

# 문서 요약 요청 엔드포인트
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
            from app.services.team_service import check_team_permission
            
            has_access = await check_team_permission(
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
            job_id=f"summarize_{document_id}_{current_user.id}",
            job_timeout=1800,  # 30분 타임아웃
            user_id=current_user.id,
            db=db,
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
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"요약 작업 등록 중 오류 발생: {str(e)}")

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
            limit=limit,
            status=status
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
    

@router.get("/get-id-by-path", response_model=Dict[str, Any])
async def get_document_id_by_path(
    file_path: str = Query(..., description="PDF 파일 경로"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """파일 경로로 문서 ID 조회"""
    try:
        from app.models.tag import PDFFile
        
        # 전체 경로로 찾기
        pdf_file = db.query(PDFFile).filter(PDFFile.file_path == file_path).first()
        
        if pdf_file:
            return {
                "success": True,
                "document_id": pdf_file.id,
                "file_path": pdf_file.file_path,
                "file_name": pdf_file.filename
            }
        
        # 파일명만으로 찾기
        file_name = os.path.basename(file_path)
        pdf_file = db.query(PDFFile).filter(PDFFile.filename == file_name).first()
        
        if pdf_file:
            return {
                "success": True,
                "document_id": pdf_file.id,
                "file_path": pdf_file.file_path,
                "file_name": pdf_file.filename
            }
        
        return {
            "success": False,
            "message": "파일을 찾을 수 없습니다",
            "file_path": file_path
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_path": file_path
        }