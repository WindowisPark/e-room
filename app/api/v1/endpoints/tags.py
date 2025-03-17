# app/api/v1/endpoints/tags.py
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.tag import (
    AnnotationCreate, 
    AnnotationUpdate, 
    AnnotationResponse, 
    AnnotationList
)
from app.services.tag_service import (
    create_pdf_annotation,
    update_pdf_annotation,
    delete_pdf_annotation,
    get_pdf_annotations,
    search_annotations
)

router = APIRouter()

@router.post("/", response_model=AnnotationResponse)
async def create_annotation(
    *,
    db: Session = Depends(get_db),
    annotation_data: AnnotationCreate,
    current_user: User = Depends(get_current_user)
):
    """PDF 주석 생성"""
    result = await create_pdf_annotation(
        db=db,
        pdf_id=annotation_data.pdf_id,
        user_id=current_user.id,
        page=annotation_data.page,
        content=annotation_data.content,
        position=annotation_data.position,
        annotation_type=annotation_data.annotation_type
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result["error"]
        )
    
    return result

@router.put("/{tag_id}", response_model=AnnotationResponse)
async def update_annotation(
    *,
    tag_id: int,
    db: Session = Depends(get_db),
    annotation_data: AnnotationUpdate,
    current_user: User = Depends(get_current_user)
):
    """PDF 주석 업데이트 (작성자만 가능)"""
    result = await update_pdf_annotation(
        db=db,
        tag_id=tag_id,
        user_id=current_user.id,
        content=annotation_data.content,
        position=annotation_data.position
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result["error"]
        )
    
    return result

@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_annotation(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """PDF 주석 삭제 (작성자만 가능)"""
    result = await delete_pdf_annotation(
        db=db,
        tag_id=tag_id,
        user_id=current_user.id
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result["error"]
        )

@router.get("/pdf/{pdf_id}", response_model=AnnotationList)
async def get_annotations(
    pdf_id: int,
    page: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """PDF 주석 목록 조회"""
    result = await get_pdf_annotations(
        db=db,
        pdf_id=pdf_id,
        user_id=current_user.id,
        page=page
    )
    
    if "error" in result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result["error"]
        )
    
    return result

@router.get("/search", response_model=List[AnnotationResponse])
async def search_tags(
    query: str = Query(..., min_length=1),
    team_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """주석 검색 (내용, 해시태그, 멘션 등)"""
    result = await search_annotations(
        db=db,
        user_id=current_user.id,
        query=query,
        team_id=team_id
    )
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result["error"]
        )
    
    return result

@router.get("/hashtag/{tag}", response_model=List[AnnotationResponse])
async def get_by_hashtag(
    tag: str,
    team_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """해시태그별 주석 조회"""
    # 해시태그는 #을 제외한 텍스트로 검색
    result = await search_annotations(
        db=db,
        user_id=current_user.id,
        query=f"#{tag}",  # 해시태그 형식으로 검색
        team_id=team_id
    )
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result["error"]
        )
    
    return result

@router.get("/mention/{username}", response_model=List[AnnotationResponse])
async def get_by_mention(
    username: str,
    team_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """멘션별 주석 조회"""
    # 멘션은 @를 제외한 사용자명으로 검색
    result = await search_annotations(
        db=db,
        user_id=current_user.id,
        query=f"@{username}",  # 멘션 형식으로 검색
        team_id=team_id
    )
    
    if isinstance(result, dict) and "error" in result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=result["error"]
        )
    
    return result