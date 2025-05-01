# app/crud/crud_task.py
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models.task import Task

def create_task_record(
    db: Session, 
    user_id: int,
    task_type: str,
    document_id: int,
    job_id: str
) -> Task:
    """작업 기록 생성"""
    db_task = Task(
        user_id=user_id,
        task_type=task_type,
        document_id=document_id,
        job_id=job_id,
        status="pending",
        progress=0
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def update_task_status(
    db: Session,
    job_id: str,
    status: str,
    progress: float = None,
    result: Dict[str, Any] = None,
    error: str = None
) -> Optional[Task]:
    """작업 상태 업데이트"""
    task = db.query(Task).filter(Task.job_id == job_id).first()
    if not task:
        return None
        
    task.status = status
    if progress is not None:
        task.progress = progress
    if result is not None:
        task.result = result
    if error is not None:
        task.error = error
        
    db.commit()
    db.refresh(task)
    return task

def get_task_by_job_id(db: Session, job_id: str) -> Optional[Task]:
    """작업 ID로 작업 조회"""
    return db.query(Task).filter(Task.job_id == job_id).first()

def get_tasks_by_user(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100
) -> List[Task]:
    """사용자별 작업 목록 조회"""
    return db.query(Task)\
        .filter(Task.user_id == user_id)\
        .order_by(Task.created_at.desc())\
        .offset(skip)\
        .limit(limit)\
        .all()