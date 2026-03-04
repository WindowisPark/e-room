# app/crud/crud_tag.py
from typing import List, Optional, Dict
from sqlalchemy.orm import Session
from app.models.tag import PDFFile, PDFTag


def get_tag_by_id(db: Session, tag_id: int) -> Optional[PDFTag]:
    return db.query(PDFTag).filter(PDFTag.id == tag_id).first()


def get_tags_by_pdf(db: Session, pdf_id: int) -> List[PDFTag]:
    return db.query(PDFTag).filter(PDFTag.pdf_id == pdf_id).all()


def get_tags_by_pdf_page(db: Session, pdf_id: int, page: int) -> List[PDFTag]:
    return db.query(PDFTag).filter(
        PDFTag.pdf_id == pdf_id,
        PDFTag.page == page
    ).all()


def get_tags_by_user(db: Session, user_id: int) -> List[PDFTag]:
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
    return db_tag


def update_tag(
    db: Session,
    tag_id: int,
    user_id: int,
    content: Optional[str] = None,
    position: Optional[Dict[str, float]] = None
) -> Optional[PDFTag]:
    db_tag = get_tag_by_id(db, tag_id)
    if not db_tag or db_tag.user_id != user_id:
        return None
    if content is not None:
        db_tag.content = content
    if position is not None:
        db_tag.position = position
    db.commit()
    db.refresh(db_tag)
    return db_tag


def delete_tag(db: Session, tag_id: int, user_id: int) -> bool:
    db_tag = get_tag_by_id(db, tag_id)
    if not db_tag or db_tag.user_id != user_id:
        return False
    db.delete(db_tag)
    db.commit()
    return True


def get_pdf_by_id(db: Session, pdf_id: int) -> Optional[PDFFile]:
    return db.query(PDFFile).filter(PDFFile.id == pdf_id).first()


def create_pdf_file(
    db: Session,
    filename: str,
    file_path: str,
    owner_id: int,
) -> PDFFile:
    db_pdf = PDFFile(
        filename=filename,
        file_path=file_path,
        owner_id=owner_id,
    )
    db.add(db_pdf)
    db.commit()
    db.refresh(db_pdf)
    return db_pdf


def delete_pdf_file(db: Session, pdf_id: int, user_id: int, is_admin: bool = False) -> bool:
    db_pdf = get_pdf_by_id(db, pdf_id)
    if not db_pdf or (db_pdf.owner_id != user_id and not is_admin):
        return False
    db.delete(db_pdf)
    db.commit()
    return True


def get_pdf_files_by_user(db: Session, user_id: int) -> List[PDFFile]:
    return db.query(PDFFile).filter(PDFFile.owner_id == user_id).all()


def rename_pdf_file(db: Session, pdf_id: int, new_name: str, new_path: str) -> bool:
    pdf = db.query(PDFFile).filter(PDFFile.id == pdf_id).first()
    if not pdf:
        return False
    pdf.filename = new_name
    pdf.file_path = new_path
    db.commit()
    return True
