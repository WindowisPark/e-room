# app/api/v1/endpoints/question.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import crud, schemas
from app.api import deps
from app.core.redis_helper import is_attendance_checked, mark_attendance
from sqlalchemy.exc import IntegrityError

router = APIRouter()

@router.post("/question", response_model=schemas.Question)
def create_question(
    question_data: schemas.QuestionCreate,
    db: Session = Depends(deps.get_db),
    current_user: schemas.User = Depends(deps.get_current_user)
):
    try:
        # 트랜잭션 시작
        db.begin()

        # 1. 질문 생성
        new_question = crud.crud_question.create(
            db=db, obj_in=question_data, user_id=current_user.id
        )

        # 2. 출석 체크 (Redis + DB)
        if not is_attendance_checked(current_user.id):
            # DB에 출석 기록
            crud.crud_attendance.upsert_attendance(db, user_id=current_user.id)
            # Redis에 출석 기록
            mark_attendance(current_user.id)

        # 트랜잭션 커밋
        db.commit()

    except IntegrityError as e:
        db.rollback()
        raise HTTPException(status_code=409, detail="Database integrity error")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

    return new_question
