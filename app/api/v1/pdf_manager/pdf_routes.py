from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Path, Query, Body
from typing import List
from sqlalchemy.orm import Session
from app.services.file_service import FileStorageManager, FileOperationError
from app.schemas.file import (
    MultiUploadResult,
    FileRenameResponse,
    FileMoveResponse,
    FolderResponse,
    FileInfo
)
from app.api import deps
from app.models.user import User
from app.crud.crud_tag import create_pdf_file

router = APIRouter(tags=["PDF Manager"])

def get_storage_manager() -> FileStorageManager:
    return FileStorageManager()


@router.post(
    "/users/{user_id}/folders/{folder_name}/files",
    response_model=MultiUploadResult,
    summary="다중 PDF 업로드"
)
async def upload_pdf(
    user_id: int,
    folder_name: str = Path(..., min_length=1),
    files: List[UploadFile] = File(...),
    storage: FileStorageManager = Depends(get_storage_manager),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    try:
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="다른 사용자의 폴더에 파일을 업로드할 수 없습니다.")

        results = await storage.save_multiple_pdfs(user_id, folder_name, files)

        if len(results["success"]) == 0:
            raise HTTPException(status_code=400, detail="업로드에 실패한 파일이 존재합니다.")

        from app.services.point_service import add_points, PointActionType

        for file_info in results["success"]:
            await add_points(
                db=db,
                user_id=user_id,
                action_type=PointActionType.PDF_UPLOAD,
                description=f"PDF 업로드: {file_info.get('original_name', '파일')}"
            )

            create_pdf_file(
                db=db,
                filename=file_info["saved_name"],
                file_path=file_info["path"],
                owner_id=user_id
            )

        return MultiUploadResult(**results)

    except FileOperationError as e:
        raise HTTPException(e.code, detail=e.message)


@router.get(
    "/users/{user_id}/folders/{folder_name}/files",
    response_model=List[str],
    summary="폴더 내 파일 목록 조회"
)
async def get_files(
    user_id: int,
    folder_name: str,
    storage: FileStorageManager = Depends(get_storage_manager)
):
    try:
        return storage.list_files(user_id, folder_name)
    except FileOperationError as e:
        raise HTTPException(e.code, e.message)


@router.put(
    "/users/{user_id}/folders/{folder_name}",
    summary="폴더 생성",
)
async def create_folder(
    user_id: int,
    folder_name: str,
    storage: FileStorageManager = Depends(get_storage_manager)
):
    try:
        folder_path = storage.create_folder(user_id, folder_name)
        return {
            "operation": "create_folder",
            "path": str(folder_path)
        }
    except FileOperationError as e:
        raise HTTPException(e.code, e.message)


@router.delete(
    "/users/{user_id}/folders/{folder_name}/files/{file_name}",
    summary="파일 삭제"
)
async def delete_file(
    user_id: int,
    folder_name: str,
    file_name: str,
    storage: FileStorageManager = Depends(get_storage_manager)
):
    try:
        storage.delete_file(user_id, folder_name, file_name)
        return {
            "operation": "delete_file",
            "target": file_name,
            "status": "success"
        }
    except FileOperationError as e:
        raise HTTPException(e.code, e.message)


@router.delete(
    "/users/{user_id}/folders/{folder_name}",
    summary="폴더 삭제"
)
async def delete_folder(
    user_id: int,
    folder_name: str,
    storage: FileStorageManager = Depends(get_storage_manager)
):
    try:
        storage.delete_folder(user_id, folder_name)
        return {
            "operation": "delete_folder",
            "target": folder_name,
            "status": "success"
        }
    except FileOperationError as e:
        raise HTTPException(e.code, e.message)


@router.put(
    "/users/{user_id}/folders/{folder_name}/files/{file_name}/rename",
    response_model=FileRenameResponse,
    summary="파일 이름 변경"
)
async def rename_file(
    user_id: int,
    folder_name: str,
    file_name: str,
    new_name: str = Query(...),
    storage: FileStorageManager = Depends(get_storage_manager)
):
    try:
        new_path = storage.rename_file(user_id, folder_name, file_name, new_name)
        return FileRenameResponse(
            operation="rename",
            original_name=file_name,
            new_name=new_path.name,
            new_path=str(new_path),
            status="success"
        )
    except FileOperationError as e:
        raise HTTPException(e.code, e.message)


@router.put(
    "/users/{user_id}/folders/{old_folder}/move",
    response_model=FileMoveResponse,
    summary="폴더 이동"
)
async def move_folder(
    user_id: int,
    old_folder: str,
    new_folder: str,
    create_if_not_exists: bool = Query(False),
    storage: FileStorageManager = Depends(get_storage_manager)
):
    try:
        new_path = storage.move_folder(user_id, old_folder, new_folder, create_if_not_exists)
        return FileMoveResponse(
            operation="move_folder",
            original_path=f"/{user_id}/{old_folder}",
            new_path=str(new_path),
            folder_created=create_if_not_exists,
            status="success"
        )
    except FileOperationError as e:
        raise HTTPException(e.code, e.message)


@router.put(
    "/users/{user_id}/folders/{old_folder}/files/{file_name}/move",
    response_model=FileMoveResponse,
    summary="파일 이동"
)
async def move_file(
    user_id: int,
    old_folder: str,
    file_name: str,
    new_folder: str = Query(...),
    create_if_not_exists: bool = Query(False),
    storage: FileStorageManager = Depends(get_storage_manager)
):
    try:
        new_path = storage.move_file(user_id, old_folder, file_name, new_folder, create_if_not_exists)
        return FileMoveResponse(
            operation="move_file",
            original_path=f"/{user_id}/{old_folder}/{file_name}",
            new_path=str(new_path),
            folder_created=create_if_not_exists,
            status="success"
        )
    except FileOperationError as e:
        raise HTTPException(e.code, e.message)


@router.get(
    "/users/{user_id}/folders",
    response_model=List[FolderResponse],
    summary="사용자 폴더 구조 조회"
)
async def list_folders(
    user_id: int,
    include_subfolders: bool = False,
    skip: int = 0,
    limit: int = 100,
    storage: FileStorageManager = Depends(get_storage_manager)
):
    try:
        return storage.list_folders(user_id, include_subfolders, skip, limit)
    except FileOperationError as e:
        raise HTTPException(e.code, e.message)
