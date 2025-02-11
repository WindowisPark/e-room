from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.api import deps
from app.models.user import User
from app.schemas.user import UserResponse, ErrorResponse
from app.crud.crud_user import user as user_crud
from contextlib import contextmanager

router = APIRouter()

@contextmanager
def get_db_transaction(db: Session):
    """
    📌 트랜잭션을 안전하게 처리하는 컨텍스트 매니저
    """
    try:
        yield
        db.commit()
    except Exception:
        db.rollback()
        raise


@router.get(
    "/users",
    response_model=List[UserResponse],
    summary="모든 사용자 목록 조회",
    description="관리자만 접근 가능한 전체 사용자 목록 조회 API입니다.",
    responses={403: {"model": ErrorResponse}},
)
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(deps.get_admin_user)
):
    """
    📌 ✅ 관리자만 접근 가능한 전체 사용자 목록 조회 API
    - `skip`: 건너뛸 사용자 수 (페이지네이션)
    - `limit`: 가져올 사용자 수 (기본값: 100)
    """
    return user_crud.get_multi(db, skip=skip, limit=limit)


@router.put(
    "/users/{user_id}/deactivate",
    response_model=UserResponse,
    summary="사용자 계정 비활성화",
    description="관리자가 특정 사용자의 계정을 비활성화합니다.",
    responses={404: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    status_code=status.HTTP_200_OK,
)
async def deactivate_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(deps.get_admin_user)
):
    """
    📌 ✅ 사용자 계정 비활성화 API (관리자 전용)
    """
    db_user = user_crud.get(db, id=user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")

    db_user.is_active = False
    db.commit()
    db.refresh(db_user)
    return db_user


@router.delete(
    "/users/{user_id}",
    response_model=dict,
    summary="사용자 삭제",
    description="관리자가 특정 사용자를 삭제합니다.",
    responses={404: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
    status_code=status.HTTP_200_OK,
)
async def delete_user(
    user_id: int,
    db: Session = Depends(deps.get_db),
    admin_user: User = Depends(deps.get_admin_user)
):
    """
    📌 ✅ 사용자 삭제 API (관리자 전용)
    """
    with get_db_transaction(db):
        db_user = user_crud.get(db, id=user_id)
        if not db_user:
            raise HTTPException(status_code=404, detail="사용자를 찾을 수 없습니다.")
        db.delete(db_user)
    return {"message": "사용자가 삭제되었습니다."}
