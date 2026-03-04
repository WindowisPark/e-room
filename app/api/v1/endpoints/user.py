# app/api/v1/endpoints/user.py

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import os

from app.api import deps
from app.models.user import User
from app.models.tag import PDFFile, PDFTag

router = APIRouter()


@router.get("/me")
def get_me(current_user: User = Depends(deps.get_current_user)):
    """현재 로그인된 사용자 기본 정보"""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role,
        "is_active": current_user.is_active,
        "is_admin": current_user.is_admin,
        "is_verified": current_user.is_verified,
        "oauth_provider": current_user.oauth_provider,
        "created_at": current_user.created_at,
    }


@router.get("/me/details")
def get_user_details(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """현재 사용자 상세 정보 (스토리지, 활동 통계)"""
    days_since_signup = (datetime.now(timezone.utc) - current_user.created_at).days

    pdfs = db.query(PDFFile).filter(PDFFile.owner_id == current_user.id).all()
    storage_used_mb = sum(
        os.path.getsize(pdf.file_path)
        for pdf in pdfs
        if os.path.exists(pdf.file_path)
    ) / (1024 * 1024)

    annotations_count = db.query(PDFTag).filter(PDFTag.user_id == current_user.id).count()

    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "is_active": current_user.is_active,
            "is_admin": current_user.is_admin,
            "is_verified": current_user.is_verified,
            "oauth_provider": current_user.oauth_provider,
            "created_at": current_user.created_at,
        },
        "signup_info": {
            "signup_date": current_user.created_at,
            "days_since_signup": days_since_signup,
        },
        "storage": {
            "total_pdfs": len(pdfs),
            "storage_used_mb": round(storage_used_mb, 2),
        },
        "activity": {
            "annotations_count": annotations_count,
            "total_pdfs": len(pdfs),
        },
    }


@router.put("/me")
def update_me(
    full_name: str = None,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """사용자 기본 정보 수정"""
    if full_name is not None:
        current_user.full_name = full_name
    db.commit()
    db.refresh(current_user)
    return {"id": current_user.id, "full_name": current_user.full_name}


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """계정 삭제"""
    db.delete(current_user)
    db.commit()
