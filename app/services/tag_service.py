# app/services/tag_service.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.crud.crud_tag import (
    get_tag_by_id,
    get_tags_by_pdf,
    get_tags_by_pdf_page,
    create_tag,
    update_tag,
    delete_tag,
    get_pdf_by_id
)
from app.crud.crud_team import check_user_in_team
from app.services.notification_service import create_mention_notifications
from app.core.pdf_processor import PDFProcessor

async def create_pdf_annotation(
    db: Session,
    pdf_id: int,
    user_id: int,
    page: int,
    content: str,
    position: Dict[str, float],
    annotation_type: str = "highlight"
) -> Dict[str, Any]:
    """PDF 주석 생성"""
    # PDF 파일 존재 여부 및 접근 권한 확인
    pdf_file = get_pdf_by_id(db=db, pdf_id=pdf_id)
    if not pdf_file:
        return {"error": "PDF 파일을 찾을 수 없습니다"}
    
    # 팀스페이스에 속한 PDF인 경우 권한 확인
    if pdf_file.team_id:
        if not check_user_in_team(db=db, team_id=pdf_file.team_id, user_id=user_id):
            return {"error": "이 PDF에 주석을 작성할 권한이 없습니다"}
    # 개인 PDF인 경우 소유자인지 확인
    elif pdf_file.owner_id != user_id:
        return {"error": "이 PDF에 주석을 작성할 권한이 없습니다"}
    
    # 주석 생성
    tag = create_tag(
        db=db,
        pdf_id=pdf_id,
        user_id=user_id,
        page=page,
        content=content,
        position=position,
        annotation_type=annotation_type
    )
    
    # 멘션 처리 및 알림 생성
    mentions, hashtags = PDFProcessor.parse_mentions_and_tags(content)
    if mentions:
        await create_mention_notifications(
            db=db,
            tag_id=tag.id,
            team_id=pdf_file.team_id,
            mentioned_usernames=mentions,
            mentioner_id=user_id
        )
    
    # 응답 데이터 구성
    return {
        "id": tag.id,
        "pdf_id": pdf_id,
        "user_id": user_id,
        "username": tag.user.username,
        "page": page,
        "content": content,
        "position": position,
        "annotation_type": annotation_type,
        "created_at": tag.created_at.isoformat(),
        "mentions": mentions,
        "hashtags": hashtags
    }

async def update_pdf_annotation(
    db: Session,
    tag_id: int,
    user_id: int,
    content: Optional[str] = None,
    position: Optional[Dict[str, float]] = None
) -> Optional[Dict[str, Any]]:
    """PDF 주석 업데이트"""
    # 기존 태그 조회
    tag = get_tag_by_id(db=db, tag_id=tag_id)
    if not tag:
        return {"error": "주석을 찾을 수 없습니다"}
    
    # 권한 확인 (본인 작성 주석만 수정 가능)
    if tag.user_id != user_id:
        return {"error": "이 주석을 수정할 권한이 없습니다"}
    
    # 업데이트 실행
    updated_tag = update_tag(
        db=db,
        tag_id=tag_id,
        user_id=user_id,
        content=content,
        position=position
    )
    
    if not updated_tag:
        return {"error": "주석 업데이트에 실패했습니다"}
    
    # 멘션 처리 및 알림 생성 (내용이 변경된 경우만)
    if content:
        mentions, hashtags = PDFProcessor.parse_mentions_and_tags(content)
        if mentions:
            await create_mention_notifications(
                db=db,
                tag_id=tag.id,
                team_id=tag.pdf_file.team_id,
                mentioned_usernames=mentions,
                mentioner_id=user_id
            )
    else:
        mentions, hashtags = [], []
    
    # 응답 데이터 구성
    return {
        "id": updated_tag.id,
        "pdf_id": updated_tag.pdf_id,
        "user_id": updated_tag.user_id,
        "username": updated_tag.user.username,
        "page": updated_tag.page,
        "content": updated_tag.content,
        "position": updated_tag.position,
        "annotation_type": updated_tag.annotation_type,
        "created_at": updated_tag.created_at.isoformat(),
        "mentions": mentions,
        "hashtags": hashtags
    }

async def delete_pdf_annotation(db: Session, tag_id: int, user_id: int) -> Dict[str, Any]:
    """PDF 주석 삭제"""
    # 기존 태그 조회
    tag = get_tag_by_id(db=db, tag_id=tag_id)
    if not tag:
        return {"error": "주석을 찾을 수 없습니다"}
    
    # 권한 확인 (본인 작성 주석만 삭제 가능)
    if tag.user_id != user_id:
        return {"error": "이 주석을 삭제할 권한이 없습니다"}
    
    # 삭제 실행
    success = delete_tag(db=db, tag_id=tag_id, user_id=user_id)
    
    if not success:
        return {"error": "주석 삭제에 실패했습니다"}
    
    return {"success": True, "message": "주석이 삭제되었습니다"}

async def get_pdf_annotations(db: Session, pdf_id: int, user_id: int, page: Optional[int] = None) -> Dict[str, Any]:
    """PDF 주석 목록 조회"""
    # PDF 파일 존재 여부 및 접근 권한 확인
    pdf_file = get_pdf_by_id(db=db, pdf_id=pdf_id)
    if not pdf_file:
        return {"error": "PDF 파일을 찾을 수 없습니다"}
    
    # 팀스페이스에 속한 PDF인 경우 권한 확인
    if pdf_file.team_id:
        if not check_user_in_team(db=db, team_id=pdf_file.team_id, user_id=user_id):
            return {"error": "이 PDF의 주석을 조회할 권한이 없습니다"}
    # 개인 PDF인 경우 소유자인지 확인
    elif pdf_file.owner_id != user_id:
        return {"error": "이 PDF의 주석을 조회할 권한이 없습니다"}
    
    # 주석 조회
    if page is not None:
        tags = get_tags_by_pdf_page(db=db, pdf_id=pdf_id, page=page)
    else:
        tags = get_tags_by_pdf(db=db, pdf_id=pdf_id)
    
    # 응답 데이터 구성
    annotations = []
    for tag in tags:
        mentions, hashtags = PDFProcessor.parse_mentions_and_tags(tag.content)
        annotations.append({
            "id": tag.id,
            "pdf_id": pdf_id,
            "user_id": tag.user_id,
            "username": tag.user.username,
            "page": tag.page,
            "content": tag.content,
            "position": tag.position,
            "annotation_type": tag.annotation_type,
            "created_at": tag.created_at.isoformat(),
            "mentions": mentions,
            "hashtags": hashtags
        })
    
    return {
        "pdf_id": pdf_id,
        "file_name": pdf_file.filename,
        "page": page,
        "annotations": annotations
    }

async def search_annotations(
    db: Session, 
    user_id: int, 
    query: str, 
    team_id: Optional[int] = None
) -> List[Dict[str, Any]]:
    """주석 검색 (내용, 해시태그, 멘션 등)"""
    # 팀 지정된 경우 팀 멤버인지 확인
    if team_id:
        if not check_user_in_team(db=db, team_id=team_id, user_id=user_id):
            return {"error": "이 팀의 주석을 검색할 권한이 없습니다"}
    
    # 주석 조회 쿼리 구성
    from sqlalchemy import or_
    from app.models.tag import PDFTag, PDFFile
    
    base_query = (
        db.query(PDFTag)
        .join(PDFFile, PDFTag.pdf_id == PDFFile.id)
    )
    
    # 팀 지정된 경우 해당 팀의 PDF만 조회
    if team_id:
        base_query = base_query.filter(PDFFile.team_id == team_id)
    else:
        # 팀 지정 안된 경우 사용자가 접근 가능한 PDF만 조회
        from app.models.team import TeamMember
        
        team_ids = (
            db.query(TeamMember.team_id)
            .filter(TeamMember.user_id == user_id)
        )
        
        base_query = base_query.filter(
            or_(
                PDFFile.owner_id == user_id,  # 개인 소유 PDF
                PDFFile.team_id.in_(team_ids)  # 속한 팀의 PDF
            )
        )
    
    # 검색어로 필터링
    search_results = base_query.filter(
        or_(
            PDFTag.content.ilike(f"%{query}%"),  # 내용 검색
            PDFTag.content.ilike(f"%#{query}%"),  # 해시태그 검색
            PDFTag.content.ilike(f"%@{query}%")   # 멘션 검색
        )
    ).all()
    
    # 응답 데이터 구성
    results = []
    for tag in search_results:
        mentions, hashtags = PDFProcessor.parse_mentions_and_tags(tag.content)
        results.append({
            "id": tag.id,
            "pdf_id": tag.pdf_id,
            "file_name": tag.pdf_file.filename,
            "team_id": tag.pdf_file.team_id,
            "user_id": tag.user_id,
            "username": tag.user.username,
            "page": tag.page,
            "content": tag.content,
            "snippet": tag.content[:100] + "..." if len(tag.content) > 100 else tag.content,
            "position": tag.position,
            "annotation_type": tag.annotation_type,
            "created_at": tag.created_at.isoformat(),
            "mentions": mentions,
            "hashtags": hashtags
        })
    
    return results