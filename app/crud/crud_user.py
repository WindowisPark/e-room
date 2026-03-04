# app/crud/crud_user.py
from typing import Optional, List
from sqlalchemy.orm import Session
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserCreateOAuth, UserUpdate
from sqlalchemy.exc import SQLAlchemyError
from app.core.exceptions import DatabaseException, NotFoundException, ErrorMessage

class CRUDUser:
    def get(self, db: Session, id: int) -> Optional[User]:
        """📌 ID로 사용자 조회"""
        return db.query(User).filter(User.id == id).first()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        """📌 이메일로 사용자 조회"""
        return db.query(User).filter(User.email == email).first()

    def get_by_oauth_id(self, db: Session, oauth_provider: str, oauth_id: str) -> Optional[User]:
        """📌 OAuth 사용자 조회"""
        return db.query(User).filter(
            User.oauth_provider == oauth_provider,
            User.oauth_id == oauth_id
        ).first()

    def get_multi(self, db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        """📌 여러 사용자 조회 (페이지네이션)"""
        return db.query(User).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        """📌 일반 사용자 생성"""
        try:
            db_obj = User(
                email=obj_in.email,
                username=obj_in.username,
                full_name=obj_in.full_name,
                hashed_password=get_password_hash(obj_in.password)
            )
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseException(f"사용자 생성 실패: {str(e)}")

    def create_oauth_user(self, db: Session, *, obj_in: UserCreateOAuth) -> User:
        """📌 OAuth 사용자 생성"""
        try:
            db_obj = User(
                email=obj_in.email,
                full_name=obj_in.full_name,
                oauth_provider=obj_in.oauth_provider,
                oauth_id=obj_in.oauth_id
            )
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseException(f"OAuth 사용자 생성 실패: {str(e)}")

    def update(self, db: Session, *, db_obj: User, obj_in: UserUpdate) -> User:
        """📌 사용자 정보 업데이트"""
        try:
            if isinstance(obj_in, dict):
                update_data = obj_in
            else:
                update_data = obj_in.dict(exclude_unset=True)

            if "password" in update_data:
                update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

            for field, value in update_data.items():
                setattr(db_obj, field, value)

            db.commit()
            db.refresh(db_obj)
            return db_obj
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseException(f"사용자 업데이트 실패: {str(e)}")

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        """📌 사용자 인증"""
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        """📌 활성화된 사용자 확인"""
        return user.is_active  # `disabled` 대신 `is_active` 필드 사용

    def is_admin(self, user: User) -> bool:
        """📌 관리자인지 확인"""
        return user.is_admin

    def delete(self, db: Session, *, user_id: int) -> None:
        """📌 사용자 삭제"""
        try:
            user = self.get(db, user_id)
            if not user:
                raise NotFoundException(ErrorMessage.USER_NOT_FOUND)

            db.delete(user)
            db.commit()
        except SQLAlchemyError as e:
            db.rollback()
            raise DatabaseException(f"사용자 삭제 실패: {str(e)}")

user = CRUDUser()