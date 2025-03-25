# app/crud/crud_tag.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models.tag import PDFFile, PDFTag, PDFTagMention
from app.models.user import User
from app.core.pdf_processor import PDFProcessor

def get_tag_by_id(db: Session, tag_id: int) -> Optional[PDFTag]:
    """ID로 태그/주석 조회"""
    return db.query(PDFTag).filter(PDFTag.id == tag_id).first()

def get_tags_by_pdf(db: Session, pdf_id: int) -> List[PDFTag]:
    """PDF ID로 모든 태그/주석 조회"""
    return db.query(PDFTag).filter(PDFTag.pdf_id == pdf_id).all()

def get_tags_by_pdf_page(db: Session, pdf_id: int, page: int) -> List[PDFTag]:
    """PDF의 특정 페이지에 있는 태그/주석 조회"""
    return db.query(PDFTag).filter(
        PDFTag.pdf_id == pdf_id,
        PDFTag.page == page
    ).all()

def get_tags_by_user(db: Session, user_id: int) -> List[PDFTag]:
    """사용자가 작성한 모든 태그/주석 조회"""
    return db.query(PDFTag).filter(PDFTag.user_id == user_id).all()

def create_tag(
    db: Session, 
    pdf_id: int, 
    user_id: int, 
    page: int, 
    content: str, 
    position: Dict[str, float],
    annotation_type: str = "highlight"
) -> PDFTag:
    """새 태그/주석 생성"""
    db_tag = PDFTag(
        pdf_id=pdf_id,
        user_id=user_id,
        page=page,
        content=content,
        position=position,
        annotation_type=annotation_type
    )
    db.add(db_tag)
    db.commit()
    db.refresh(db_tag)
    
    # 멘션 처리
    mentions, _ = PDFProcessor.parse_mentions_and_tags(content)
    if mentions:
        process_mentions(db, db_tag.id, mentions)
    
    return db_tag

def update_tag(
    db: Session, 
    tag_id: int, 
    user_id: int, 
    content: Optional[str] = None, 
    position: Optional[Dict[str, float]] = None
) -> Optional[PDFTag]:
    """태그/주석 업데이트 (작성자만 가능)"""
    db_tag = get_tag_by_id(db, tag_id)
    if not db_tag or db_tag.user_id != user_id:
        return None
    
    # 업데이트 필드 처리
    if content is not None:
        db_tag.content = content
        
        # 멘션 업데이트
        db.query(PDFTagMention).filter(PDFTagMention.tag_id == tag_id).delete()
        mentions, _ = PDFProcessor.parse_mentions_and_tags(content)
        if mentions:
            process_mentions(db, db_tag.id, mentions)
    
    if position is not None:
        db_tag.position = position
    
    db.commit()
    db.refresh(db_tag)
    return db_tag

def delete_tag(db: Session, tag_id: int, user_id: int) -> bool:
    """태그/주석 삭제 (작성자만 가능)"""
    db_tag = get_tag_by_id(db, tag_id)
    if not db_tag or db_tag.user_id != user_id:
        return False
    
    db.delete(db_tag)
    db.commit()
    return True

def process_mentions(db: Session, tag_id: int, usernames: List[str]) -> None:
    """태그/주석 내 멘션된 사용자들 처리"""
    for username in usernames:
        # 사용자 조회
        user = db.query(User).filter(User.username == username).first()
        if user:
            # 멘션 생성
            db_mention = PDFTagMention(
                tag_id=tag_id,
                mentioned_user_id=user.id
            )
            db.add(db_mention)
    
    db.commit()

def get_pdf_by_id(db: Session, pdf_id: int) -> Optional[PDFFile]:
    """ID로 PDF 파일 조회"""
    return db.query(PDFFile).filter(PDFFile.id == pdf_id).first()

def create_pdf_file(
    db: Session, 
    filename: str, 
    file_path: str, 
    owner_id: int, 
    team_id: Optional[int] = None
) -> PDFFile:
    """새 PDF 파일 생성"""
    db_pdf = PDFFile(
        filename=filename,
        file_path=file_path,
        owner_id=owner_id,
        team_id=team_id
    )
    db.add(db_pdf)
    db.commit()
    db.refresh(db_pdf)
    return db_pdf

def delete_pdf_file(db: Session, pdf_id: int, user_id: int, is_admin: bool = False) -> bool:
    """PDF 파일 삭제 (소유자 또는 관리자만 가능)"""
    db_pdf = get_pdf_by_id(db, pdf_id)
    
    # 파일이 없거나 삭제 권한이 없음
    if not db_pdf or (db_pdf.owner_id != user_id and not is_admin):
        return False
    
    db.delete(db_pdf)
    db.commit()
    return True

def get_pdf_files_by_team(db: Session, team_id: int) -> List[PDFFile]:
    """팀스페이스에 속한 모든 PDF 파일 조회"""
    return db.query(PDFFile).filter(PDFFile.team_id == team_id).all()

def get_pdf_files_by_user(db: Session, user_id: int) -> List[PDFFile]:
    """사용자가 소유한 모든 PDF 파일 조회"""
    return db.query(PDFFile).filter(PDFFile.owner_id == user_id).all()