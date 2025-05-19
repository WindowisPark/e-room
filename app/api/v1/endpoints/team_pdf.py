# app/api/v1/endpoints/team_pdf.py

from fastapi import APIRouter, Depends, HTTPException, status, Path, File, UploadFile, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import os

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.tag import PDFFile
from app.schemas.file import FileInfo, MultiUploadResult, FileRenameResponse
from app.schemas.team_pdf import PDFMetadata, RenamePDFRequest
from app.services.team_service import check_team_permission
from app.services.file_service import FileStorageManager
from app.crud.crud_tag import get_pdf_by_id, create_pdf_file, get_pdf_files_by_team, delete_pdf_file, rename_pdf_file

router = APIRouter()
storage_manager = FileStorageManager()

@router.post("/{team_id}/pdf", response_model=FileInfo)
async def upload_team_pdf(
    team_id: int = Path(..., ge=1),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """팀스페이스에 PDF 파일 업로드 (편집 권한 이상 필요)"""
    # 팀 멤버십 및 편집 권한 확인
    has_edit_access = await check_team_permission(
        db=db,
        team_id=team_id,
        user_id=current_user.id,
        required_role="editor"
    )
    if not has_edit_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 팀스페이스에 파일을 업로드할 권한이 없습니다"
        )

    # 파일 확장자 검증
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="PDF 파일만 업로드 가능합니다"
        )

    try:
        # 팀 전용 저장 경로
        team_folder = f"team_{team_id}"

        # 파일 저장
        file_path = await storage_manager.save_pdf(
            user_id=current_user.id,
            folder=team_folder,
            file=file
        )

        # DB에 파일 정보 저장
        db_pdf = create_pdf_file(
            db=db,
            filename=file.filename,
            file_path=file_path,
            owner_id=current_user.id,
            team_id=team_id
        )

        return {
            "id": db_pdf.id,
            "original_name": db_pdf.filename,
            "saved_name": os.path.basename(file_path),
            "size": os.path.getsize(file_path),
            "path": file_path
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 업로드 중 오류가 발생했습니다: {str(e)}"
        )

@router.post("/{team_id}/pdf/batch", response_model=MultiUploadResult)
async def upload_multiple_pdfs(
    team_id: int = Path(..., ge=1),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """팀스페이스에 여러 PDF 파일 일괄 업로드 (편집 권한 이상 필요)"""
    # 팀 멤버십 및 편집 권한 확인
    has_edit_access = await check_team_permission(
        db=db,
        team_id=team_id,
        user_id=current_user.id,
        required_role="editor"
    )
    if not has_edit_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 팀스페이스에 파일을 업로드할 권한이 없습니다"
        )

    try:
        # 팀 전용 저장 경로
        team_folder = f"team_{team_id}"

        # 파일 일괄 저장
        results = await storage_manager.save_multiple_pdfs(
            user_id=current_user.id,
            folder=team_folder,
            files=files
        )

        # DB에 성공적으로 저장된 파일 정보 저장
        for file_info in results["success"]:
            create_pdf_file(
                db=db,
                filename=file_info["original_name"],
                file_path=file_info["path"],
                owner_id=current_user.id,
                team_id=team_id
            )

        return results

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"파일 업로드 중 오류가 발생했습니다: {str(e)}"
        )

@router.get("/{team_id}/pdf", response_model=List[PDFMetadata])
async def list_team_pdfs(
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """팀스페이스의 PDF 파일 목록 조회"""
    # 팀 멤버십 확인
    has_access = await check_team_permission(
        db=db,
        team_id=team_id,
        user_id=current_user.id
    )
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 팀스페이스의 파일을 조회할 권한이 없습니다"
        )

    # 팀의 PDF 파일 목록 조회
    pdfs = get_pdf_files_by_team(db=db, team_id=team_id)

    # 응답 데이터 구성
    results = []
    for pdf in pdfs:
        results.append({
            "id": pdf.id,
            "filename": pdf.filename,
            "file_path": pdf.file_path,
            "owner_id": pdf.owner_id,
            "owner_username": pdf.owner.username,
            "created_at": pdf.created_at.isoformat()
        })

    return results

@router.delete("/{team_id}/pdf/{pdf_id}")
async def delete_team_pdf(
    team_id: int = Path(..., ge=1),
    pdf_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """팀스페이스의 PDF 파일 삭제 (편집 권한 이상 필요)"""
    # 팀 멤버십 및 편집 권한 확인
    has_edit_access = await check_team_permission(
        db=db,
        team_id=team_id,
        user_id=current_user.id,
        required_role="editor"
    )
    if not has_edit_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 팀스페이스에서 파일을 삭제할 권한이 없습니다"
        )

    # 파일 존재 여부 및 팀 소속 확인
    pdf_file = get_pdf_by_id(db=db, pdf_id=pdf_id)
    if not pdf_file:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="파일을 찾을 수 없습니다"
        )

    if pdf_file.team_id != team_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 팀스페이스에 속한 파일이 아닙니다"
        )

    # 실제 파일 삭제
    try:
        if os.path.exists(pdf_file.file_path):
            os.remove(pdf_file.file_path)
    except Exception as e:
        # 파일 시스템 오류는 로깅만 하고 계속 진행
        print(f"파일 삭제 중 오류: {str(e)}")

    # DB에서 파일 정보 삭제
    success = delete_pdf_file(
        db=db,
        pdf_id=pdf_id,
        user_id=current_user.id,
        is_admin=current_user.is_admin
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="파일 삭제 중 오류가 발생했습니다"
        )

    return {"message": "파일이 삭제되었습니다"}

@router.patch("/{team_id}/pdf/{pdf_id}/rename", response_model=FileRenameResponse)
async def rename_team_pdf(
    team_id: int = Path(..., ge=1),
    pdf_id: int = Path(..., ge=1),
    payload: RenamePDFRequest = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """팀스페이스 PDF 파일 이름 변경 (편집 권한 이상)"""
    has_edit_access = await check_team_permission(
        db=db,
        team_id=team_id,
        user_id=current_user.id,
        required_role="editor"
    )
    if not has_edit_access:
        raise HTTPException(status_code=403, detail="권한이 없습니다.")

    pdf = get_pdf_by_id(db=db, pdf_id=pdf_id)
    if not pdf or pdf.team_id != team_id:
        raise HTTPException(status_code=404, detail="파일이 존재하지 않거나 팀에 속하지 않습니다.")

    # 실제 파일 이름 변경
    old_path = pdf.file_path
    dir_path = os.path.dirname(old_path)
    new_path = os.path.join(dir_path, payload.new_name)

    try:
        os.rename(old_path, new_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 이름 변경 실패: {str(e)}")

    success = rename_pdf_file(
        db=db,
        pdf_id=pdf_id,
        new_name=payload.new_name,
        new_path=new_path
    )

    if not success:
        raise HTTPException(status_code=500, detail="DB에 파일 이름 반영 실패")

    return FileRenameResponse(
        operation="rename",
        original_name=pdf.filename,
        new_name=payload.new_name,
        new_path=new_path,
        status="success"
    )