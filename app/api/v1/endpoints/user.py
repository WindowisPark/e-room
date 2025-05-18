# app/api/v1/endpoints/user.py

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict, Any, List
import os

from app.api import deps
from app.models.user import User
from app.schemas.user import UserDetailResponse
from app.services.team_service import get_user_teams
from app.services.point_service import get_point_summary
from app.services.badge_service import get_user_badges
from app.crud.crud_notification import get_unread_notification_count
from app.crud.crud_tag import get_pdf_files_by_user
from app.models.tag import PDFTag
from app.services.payment_service import get_user_payments

router = APIRouter()

@router.get("/me/details", response_model=UserDetailResponse)
async def get_user_details(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """현재 사용자의 상세 정보 조회 (요금제, 팀 정보 등 포함)"""
    
    # 팀 정보 조회
    teams = await get_user_teams(db=db, user_id=current_user.id)
    
    # 요금제 정보
    subscription_info = {
        "plan_type": current_user.plan_type,
        "is_active": current_user.is_plan_active,
        "expires_at": current_user.plan_expires_at,
        "days_until_expiry": current_user.days_until_expiry,
        "max_team_spaces": current_user.max_team_spaces
    }
    
    # 게이미피케이션 요약 정보
    gamification_summary = get_point_summary(db, current_user.id)
    
    # 배지 정보
    badges = await get_user_badges(db, current_user.id)
    recent_badges = badges[:3]  # 최근 3개만
    
    # 알림 정보
    unread_notifications = get_unread_notification_count(db, current_user.id)
    
    # 스토리지 사용량 계산
    pdfs = get_pdf_files_by_user(db, current_user.id)
    
    storage_info = {
        "total_pdfs": len(pdfs),
        "storage_used_mb": sum(os.path.getsize(pdf.file_path) for pdf in pdfs if os.path.exists(pdf.file_path)) / (1024 * 1024),
        "storage_limit_mb": 1024 if current_user.plan_type == "free" else (5120 if current_user.plan_type == "premium" else 20480)
    }
    
    # 활동 통계
    annotations_count = db.query(PDFTag).filter(PDFTag.user_id == current_user.id).count()
    
    # 결제 정보
    recent_payments = get_user_payments(db, current_user.id, limit=1)
    
    payment_info = None
    if recent_payments:
        payment = recent_payments[0]
        payment_info = {
            "last_payment_date": payment.paid_at,
            "last_payment_amount": payment.amount,
            "next_payment_date": current_user.plan_expires_at
        }
    
    # 가입 후 경과 일수 계산
    days_since_signup = (datetime.utcnow() - current_user.created_at).days
    
    return {
        "user": {
            "id": current_user.id,
            "email": current_user.email,
            "username": current_user.username,
            "full_name": current_user.full_name,
            "is_active": current_user.is_active,
            "is_admin": current_user.is_admin,
            "created_at": current_user.created_at,
            "days_since_signup": days_since_signup,  # 가입 후 경과 일수 추가
            "is_phone_verified": current_user.is_phone_verified,
            "is_email_verified": current_user.is_verified,
            "oauth_provider": current_user.oauth_provider
        },
        "subscription": subscription_info,
        "payment": payment_info,
        "storage": storage_info,
        "teams": teams,
        "gamification": {
            "level": current_user.level,
            "points": current_user.points,
            "streak_days": current_user.streak_days,
            "level_progress": gamification_summary.level_progress_percent
        },
        "activity": {
            "annotations_count": annotations_count,
            "teams_count": len(teams),
            "badges_count": len(badges)
        },
        "notifications": {
            "unread_count": unread_notifications,
            "allow_mentions": current_user.allow_mention_notifications
        },
        "recent_badges": recent_badges
    }