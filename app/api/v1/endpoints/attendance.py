# app/api/v1/endpoints/attendance.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app import crud, schemas
from app.api import deps
from app.core.redis_helper import is_attendance_checked, mark_attendance

router = APIRouter()

@router.post("/attendance", response_model=schemas.Attendance)
def check_attendance(
    db: Session = Depends(deps.get_db),
    current_user: schemas.User = Depends(deps.get_current_user)
):
    user_id = current_user.id

    # Step 1: Redis에서 출석 여부 확인
    if is_attendance_checked(user_id):
        return {"msg": "이미 출석 체크를 완료했습니다."}

    try:
        # Step 2: 출석 정보 DB에 UPSERT
        crud.crud_attendance.upsert_attendance(db, user_id=user_id)
        db.commit()

        # Step 3: Redis에 출석 정보 기록
        mark_attendance(user_id)

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Concurrent request detected")

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")

    return {"msg": "출석 체크가 성공적으로 완료되었습니다."}
