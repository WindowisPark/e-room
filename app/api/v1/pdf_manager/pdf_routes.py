from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Path, Query
from typing import List
from app.services.file_service import FileStorageManager, FileOperationError
from app.schemas.file import (
    MultiUploadResult,
    FileRenameResponse,
    FileMoveResponse,
    FolderResponse,
    FileInfo
)

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
    storage: FileStorageManager = Depends(get_storage_manager)
):
    try:
        results = await storage.save_multiple_pdfs(user_id, folder_name, files)

        # ✅ 모든 업로드 실패 시 예외 반환
        if len(results["success"]) == 0:
            raise HTTPException(status_code=400, detail="업로드에 실패한 파일이 존재합니다.")

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
