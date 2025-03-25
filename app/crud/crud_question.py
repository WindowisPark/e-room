from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.question import Question
from app.schemas.question import QuestionCreate, QuestionUpdate

def get(db: Session, id: int) -> Optional[Question]:
    """
    ID로 질문 조회
    """
    return db.query(Question).filter(Question.id == id).first()

def get_multi(
    db: Session, *, skip: int = 0, limit: int = 100, user_id: Optional[int] = None
) -> List[Question]:
    """
    질문 목록 조회 (사용자 ID 지정 시 해당 사용자의 질문만 조회)
    """
    query = db.query(Question)
    if user_id:
        query = query.filter(Question.user_id == user_id)
    return query.offset(skip).limit(limit).all()

def create(db: Session, *, obj_in: QuestionCreate, user_id: int) -> Question:
    """
    질문 생성
    """
    db_obj = Question(
        title=obj_in.title,
        content=obj_in.content,
        user_id=user_id
    )
    db.add(db_obj)
    db.flush()  # ID를 얻기 위해 플러시 (commit 없이)
    return db_obj

def update(
    db: Session, *, db_obj: Question, obj_in: Dict[str, Any]
) -> Question:
    """
    질문 업데이트
    """
    update_data = obj_in if isinstance(obj_in, dict) else obj_in.dict(exclude_unset=True)
    
    for field in ["title", "content"]:
        if field in update_data:
            setattr(db_obj, field, update_data[field])
    
    db.add(db_obj)
    db.flush()
    return db_obj

def remove(db: Session, *, id: int, user_id: int) -> Optional[Question]:
    """
    질문 삭제 (작성자만 가능)
    """
    obj = db.query(Question).filter(Question.id == id, Question.user_id == user_id).first()
    if obj:
        db.delete(obj)
        db.flush()
    return obj