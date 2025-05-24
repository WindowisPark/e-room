# app/services/password_reset_service.py

import secrets
import string
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.models.user import User
from app.models.password_reset import PasswordResetToken
from app.services.email_service import EmailService
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)

class PasswordResetService:
    """
    비밀번호 재설정 서비스
    
    비밀번호 찾기/재설정 관련 모든 비즈니스 로직을 처리합니다.
    - 토큰 생성 및 관리
    - 이메일 발송
    - 보안 검증
    - OAuth 사용자 처리
    """
    
    def __init__(self):
        self.email_service = EmailService()
        self.token_expiry_minutes = 30  # 토큰 유효시간 30분
        self.token_length = 64  # 토큰 길이

    def generate_reset_token(self) -> str:
        """
        암호학적으로 안전한 재설정 토큰 생성
        
        Returns:
            64자리 랜덤 토큰
        """
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(self.token_length))

    async def request_password_reset(
        self, 
        db: Session, 
        email: str
    ) -> Dict[str, Any]:
        """
        비밀번호 재설정 요청 처리
        
        Args:
            db: 데이터베이스 세션
            email: 사용자 이메일
            
        Returns:
            처리 결과 정보
        """
        try:
            # 1. 사용자 조회
            user = db.query(User).filter(User.email == email).first()
            
            # 보안상 사용자가 없어도 성공 메시지 반환 (계정 존재 여부 숨김)
            if not user:
                logger.info(f"존재하지 않는 이메일로 비밀번호 재설정 요청: {email}")
                return {
                    "success": True,
                    "message": "등록된 이메일이면 비밀번호 재설정 링크를 발송했습니다.",
                    "email": email
                }

            # 2. OAuth 사용자 확인
            if user.oauth_provider:
                oauth_urls = {
                    "kakao": "https://accounts.kakao.com/weblogin/find_password",
                    "google": "https://accounts.google.com/signin/recovery",
                    "github": "https://github.com/password_reset"
                }
                
                return {
                    "success": False,
                    "message": f"{user.oauth_provider.title()} 계정입니다. {user.oauth_provider.title()}에서 비밀번호를 재설정해 주세요.",
                    "oauth_provider": user.oauth_provider,
                    "redirect_url": oauth_urls.get(user.oauth_provider)
                }

            # 3. 기존 유효한 토큰들 무효화
            self._invalidate_existing_tokens(db, user.id)

            # 4. 새 토큰 생성
            reset_token = self.generate_reset_token()
            expires_at = datetime.utcnow() + timedelta(minutes=self.token_expiry_minutes)
            
            token_record = PasswordResetToken(
                user_id=user.id,
                token=reset_token,
                expires_at=expires_at
            )
            
            db.add(token_record)
            db.commit()
            db.refresh(token_record)

            # 5. 이메일 발송
            email_sent = await self.email_service.send_password_reset_email(
                to_email=email,
                reset_token=reset_token,
                user_name=user.full_name or user.username
            )

            if not email_sent:
                # 이메일 발송 실패 시 토큰 무효화
                token_record.mark_as_used()
                db.commit()
                
                logger.error(f"비밀번호 재설정 이메일 발송 실패: {email}")
                return {
                    "success": False,
                    "message": "이메일 발송에 실패했습니다. 잠시 후 다시 시도해 주세요."
                }

            logger.info(f"비밀번호 재설정 토큰 생성 및 이메일 발송 완료: {email}")
            return {
                "success": True,
                "message": "비밀번호 재설정 링크를 이메일로 발송했습니다.",
                "email": email,
                "token_expires_in_minutes": self.token_expiry_minutes
            }

        except Exception as e:
            logger.error(f"비밀번호 재설정 요청 처리 중 오류: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": "서버 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
            }

    def validate_reset_token(
        self, 
        db: Session, 
        token: str
    ) -> Dict[str, Any]:
        """
        재설정 토큰 유효성 검사
        
        Args:
            db: 데이터베이스 세션
            token: 검증할 토큰
            
        Returns:
            검증 결과 정보
        """
        try:
            # 토큰 조회
            token_record = db.query(PasswordResetToken).filter(
                PasswordResetToken.token == token
            ).first()

            if not token_record:
                logger.warning(f"존재하지 않는 토큰으로 검증 시도: {token[:10]}...")
                return {
                    "valid": False,
                    "message": "유효하지 않은 토큰입니다."
                }

            # 토큰 유효성 검사
            if token_record.is_used:
                return {
                    "valid": False,
                    "message": "이미 사용된 토큰입니다."
                }

            if token_record.is_expired:
                return {
                    "valid": False,
                    "message": "만료된 토큰입니다. 새로운 비밀번호 재설정을 요청해 주세요."
                }

            # 사용자 존재 여부 확인
            user = db.query(User).filter(User.id == token_record.user_id).first()
            if not user:
                logger.error(f"토큰에 연결된 사용자가 존재하지 않음: user_id={token_record.user_id}")
                return {
                    "valid": False,
                    "message": "사용자 정보를 찾을 수 없습니다."
                }

            logger.info(f"토큰 검증 성공: user_id={user.id}")
            return {
                "valid": True,
                "message": "유효한 토큰입니다.",
                "expires_at": token_record.expires_at,
                "user_id": token_record.user_id,
                "user_email": user.email
            }

        except Exception as e:
            logger.error(f"토큰 검증 중 오류: {str(e)}", exc_info=True)
            return {
                "valid": False,
                "message": "토큰 검증 중 오류가 발생했습니다."
            }

    def reset_password(
        self, 
        db: Session, 
        token: str, 
        new_password: str
    ) -> Dict[str, Any]:
        """
        비밀번호 재설정 실행
        
        Args:
            db: 데이터베이스 세션
            token: 재설정 토큰
            new_password: 새 비밀번호
            
        Returns:
            재설정 결과 정보
        """
        try:
            # 1. 토큰 유효성 검사
            validation_result = self.validate_reset_token(db, token)
            if not validation_result["valid"]:
                return {
                    "success": False,
                    "message": validation_result["message"]
                }

            # 2. 사용자 조회
            user_id = validation_result["user_id"]
            user = db.query(User).filter(User.id == user_id).first()
            
            if not user:
                logger.error(f"비밀번호 재설정 시 사용자 없음: user_id={user_id}")
                return {
                    "success": False,
                    "message": "사용자를 찾을 수 없습니다."
                }

            # OAuth 사용자는 비밀번호 재설정 불가
            if user.oauth_provider:
                return {
                    "success": False,
                    "message": f"{user.oauth_provider.title()} 계정은 비밀번호를 재설정할 수 없습니다."
                }

            # 3. 새 비밀번호 해시화 및 저장
            user.hashed_password = get_password_hash(new_password)
            
            # 4. 토큰 사용 처리
            token_record = db.query(PasswordResetToken).filter(
                PasswordResetToken.token == token
            ).first()
            
            if token_record:
                token_record.mark_as_used()

            # 5. 해당 사용자의 다른 모든 유효한 토큰들도 무효화 (보안 강화)
            self._invalidate_existing_tokens(db, user_id, exclude_token_id=token_record.id if token_record else None)

            db.commit()

            logger.info(f"비밀번호 재설정 완료: user_id={user_id}, email={user.email}")
            return {
                "success": True,
                "message": "비밀번호가 성공적으로 변경되었습니다."
            }

        except Exception as e:
            db.rollback()
            logger.error(f"비밀번호 재설정 중 오류: {str(e)}", exc_info=True)
            return {
                "success": False,
                "message": "비밀번호 재설정 중 오류가 발생했습니다."
            }

    def _invalidate_existing_tokens(
        self, 
        db: Session, 
        user_id: int, 
        exclude_token_id: Optional[int] = None
    ) -> int:
        """
        사용자의 기존 유효한 토큰들 무효화
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            exclude_token_id: 제외할 토큰 ID (현재 사용 중인 토큰)
            
        Returns:
            무효화된 토큰 수
        """
        try:
            query = db.query(PasswordResetToken).filter(
                and_(
                    PasswordResetToken.user_id == user_id,
                    PasswordResetToken.is_used == False,
                    PasswordResetToken.expires_at > datetime.utcnow()
                )
            )
            
            # 특정 토큰 제외
            if exclude_token_id:
                query = query.filter(PasswordResetToken.id != exclude_token_id)
            
            # 무효화할 토큰들 조회
            tokens_to_invalidate = query.all()
            
            # 각 토큰을 사용 완료로 표시
            invalidated_count = 0
            for token in tokens_to_invalidate:
                token.mark_as_used()
                invalidated_count += 1
            
            if invalidated_count > 0:
                db.commit()
                logger.info(f"기존 토큰 {invalidated_count}개 무효화 완료: user_id={user_id}")
            
            return invalidated_count

        except Exception as e:
            logger.error(f"토큰 무효화 중 오류: {str(e)}")
            return 0

    def cleanup_expired_tokens(self, db: Session) -> int:
        """
        만료된 토큰들 정리 (배치 작업용)
        
        Args:
            db: 데이터베이스 세션
            
        Returns:
            정리된 토큰 수
        """
        try:
            # 1시간 이상 만료된 토큰들만 삭제 (안전 마진)
            cutoff_time = datetime.utcnow() - timedelta(hours=1)
            
            expired_tokens = db.query(PasswordResetToken).filter(
                PasswordResetToken.expires_at < cutoff_time
            ).all()
            
            deleted_count = len(expired_tokens)
            
            for token in expired_tokens:
                db.delete(token)
            
            db.commit()
            
            if deleted_count > 0:
                logger.info(f"만료된 토큰 {deleted_count}개 정리 완료")
            
            return deleted_count

        except Exception as e:
            db.rollback()
            logger.error(f"만료된 토큰 정리 중 오류: {str(e)}")
            return 0

    def get_user_reset_history(
        self, 
        db: Session, 
        user_id: int, 
        limit: int = 10
    ) -> list:
        """
        사용자의 비밀번호 재설정 이력 조회 (관리자용)
        
        Args:
            db: 데이터베이스 세션
            user_id: 사용자 ID
            limit: 조회 제한 수
            
        Returns:
            재설정 이력 목록
        """
        try:
            tokens = db.query(PasswordResetToken).filter(
                PasswordResetToken.user_id == user_id
            ).order_by(
                PasswordResetToken.created_at.desc()
            ).limit(limit).all()
            
            return [
                {
                    "id": token.id,
                    "created_at": token.created_at,
                    "expires_at": token.expires_at,
                    "is_used": token.is_used,
                    "used_at": token.used_at,
                    "is_expired": token.is_expired
                }
                for token in tokens
            ]

        except Exception as e:
            logger.error(f"재설정 이력 조회 중 오류: {str(e)}")
            return []