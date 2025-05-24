# app/crud/crud_password_reset.py

from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.password_reset import PasswordResetToken
from app.models.user import User

class CRUDPasswordReset:
    """비밀번호 재설정 토큰 CRUD 연산"""

    def get_by_token(self, db: Session, token: str) -> Optional[PasswordResetToken]:
        """토큰으로 재설정 레코드 조회"""
        return db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token
        ).first()

    def get_by_user_id(
        self, 
        db: Session, 
        user_id: int, 
        valid_only: bool = False
    ) -> List[PasswordResetToken]:
        """사용자 ID로 재설정 토큰들 조회"""
        query = db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user_id
        )
        
        if valid_only:
            query = query.filter(
                and_(
                    PasswordResetToken.is_used == False,
                    PasswordResetToken.expires_at > datetime.utcnow()
                )
            )
        
        return query.order_by(PasswordResetToken.created_at.desc()).all()

    def create(
        self, 
        db: Session, 
        user_id: int, 
        token: str, 
        expires_at: datetime
    ) -> PasswordResetToken:
        """새 재설정 토큰 생성"""
        db_token = PasswordResetToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        db.add(db_token)
        db.commit()
        db.refresh(db_token)
        return db_token

    def mark_as_used(self, db: Session, token: str) -> bool:
        """토큰을 사용 완료로 표시"""
        db_token = self.get_by_token(db, token)
        if db_token:
            db_token.mark_as_used()
            db.commit()
            return True
        return False

    def invalidate_user_tokens(
        self, 
        db: Session, 
        user_id: int, 
        exclude_token_id: Optional[int] = None
    ) -> int:
        """사용자의 유효한 토큰들 무효화"""
        query = db.query(PasswordResetToken).filter(
            and_(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.is_used == False,
                PasswordResetToken.expires_at > datetime.utcnow()
            )
        )
        
        if exclude_token_id:
            query = query.filter(PasswordResetToken.id != exclude_token_id)
        
        tokens = query.all()
        
        for token in tokens:
            token.mark_as_used()
        
        db.commit()
        return len(tokens)

    def delete_expired(self, db: Session, before_hours: int = 1) -> int:
        """만료된 토큰들 삭제"""
        cutoff_time = datetime.utcnow() - timedelta(hours=before_hours)
        
        expired_tokens = db.query(PasswordResetToken).filter(
            PasswordResetToken.expires_at < cutoff_time
        ).all()
        
        deleted_count = len(expired_tokens)
        
        for token in expired_tokens:
            db.delete(token)
        
        db.commit()
        return deleted_count

    def get_statistics(self, db: Session, days: int = 30) -> dict:
        """재설정 통계 조회 (관리자용)"""
        since_date = datetime.utcnow() - timedelta(days=days)
        
        total_requests = db.query(PasswordResetToken).filter(
            PasswordResetToken.created_at >= since_date
        ).count()
        
        successful_resets = db.query(PasswordResetToken).filter(
            and_(
                PasswordResetToken.created_at >= since_date,
                PasswordResetToken.is_used == True
            )
        ).count()
        
        expired_unused = db.query(PasswordResetToken).filter(
            and_(
                PasswordResetToken.created_at >= since_date,
                PasswordResetToken.is_used == False,
                PasswordResetToken.expires_at < datetime.utcnow()
            )
        ).count()
        
        return {
            "period_days": days,
            "total_requests": total_requests,
            "successful_resets": successful_resets,
            "expired_unused": expired_unused,
            "success_rate": (successful_resets / total_requests * 100) if total_requests > 0 else 0
        }

# 인스턴스 생성
crud_password_reset = CRUDPasswordReset()