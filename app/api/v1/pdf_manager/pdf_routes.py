# app/api/v1/pdf_manager/pdf_routes.py

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Path, Query
from typing import List
from app.services.file_service import FileStorageManager, FileOperationError, FolderResponse

router = APIRouter(prefix="/api/storage", tags=["PDF Manager"])

# 의존성 주입
def get_storage_manager() -> FileStorageManager:
    return FileStorageManager()

@router.post("/users/{user_id}/folders/{folder_name}/files", 
            summary="단일/다중 PDF 파일 업로드",
            description="PDF 파일을 한 개씩 순차적으로 업로드합니다.")
async def upload_pdf(
    user_id: int = Path(...),
    folder_name: str = Path(..., min_length=1, regex="^[a-zA-Z0-9ㄱ-ㅎ가-힣_\-(). ]+$"),
    files: List[UploadFile] = File(...),
    storage: FileStorageManager = Depends(get_storage_manager)
):
    
    """📌 여러 개의 PDF 파일 업로드 (비동기)"""
    
    saved_files = []
    
    for file in files:
        if not file.filename.lower().endswith(".pdf"):
            raise HTTPException(400, "PDF 파일만 업로드 가능합니다")
        
        file_path = await storage.save_pdf(user_id, folder_name, file)
        saved_files.append({
            "filename": file.filename,
            "path": file_path
        })

    return {
        "operation": "upload",
        "user_id": user_id,
        "files": saved_files,
        "detail": f"{len(saved_files)}개의 파일이 업로드되었습니다."
    }

@router.get("/users/{user_id}/folders/{folder_name}/files", response_model=List[str])
async def get_files(
    user_id: int,
    folder_name: str = Path(..., regex="^[a-zA-Z0-9ㄱ-ㅎ가-힣_\-(). ]+$"),
    storage: FileStorageManager = Depends(get_storage_manager)
):
    """📌 파일 목록 조회 API"""
    try:
        file_list = storage.list_files(user_id, folder_name)
        return file_list
    except FileOperationError as e:
        raise HTTPException(status_code=e.code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 목록 조회 실패: {str(e)}")

@router.put("/users/{user_id}/folders/{folder_name}")
async def create_folder(
    user_id: int,
    folder_name: str = Path(..., regex="^[a-zA-Z0-9ㄱ-ㅎ가-힣_\-(). ]+$"),
    storage: FileStorageManager = Depends(get_storage_manager)
):
    """📌 폴더 생성 (멱등성 보장)"""
    try:
        folder_path = storage.create_folder(user_id, folder_name)
        return {
            "operation": "create_folder",
            "path": str(folder_path),
            "exist_ok": folder_path.exists()
        }
    except Exception as e:
        raise HTTPException(400, str(e))

@router.delete("/users/{user_id}/folders/{folder_name}/files/{file_name}")
async def remove_file(
    user_id: int,
    folder_name: str = Path(..., regex="^[a-zA-Z0-9ㄱ-ㅎ가-힣_\-(). ]+$"),
    file_name: str = Path(..., regex="^[a-zA-Z0-9ㄱ-ㅎ가-힣_\-(). ]+$"),
    storage: FileStorageManager = Depends(get_storage_manager)
):
    """📌 파일 삭제"""
    storage.delete_file(user_id, folder_name, file_name)
    return {
        "operation": "delete_file",
        "target": file_name,
        "status": "success"
    }

@router.delete("/users/{user_id}/folders/{folder_name}")
async def remove_folder(
    user_id: int,
    folder_name: str = Path(..., regex="^[a-zA-Z0-9ㄱ-ㅎ가-힣_\-(). ]+$"),
    storage: FileStorageManager = Depends(get_storage_manager)
):
    """📌 폴더 재귀적 삭제"""
    storage.delete_folder(user_id, folder_name)
    return {
        "operation": "delete_folder",
        "target": folder_name,
        "recursive": True
    }

# 배치 업로드 엔드포인트 (병렬 처리)
@router.post("/users/{user_id}/folders/{folder_name}/batch-upload",  # URL 경로 변경
            summary="다중 PDF 일괄 업로드 (병렬)",
            description="최대 10개의 PDF 파일을 병렬로 일괄 업로드합니다.")
async def upload_multiple_pdfs(
    user_id: int,
    folder_name: str = Path(..., regex="^[a-zA-Z0-9ㄱ-ㅎ가-힣_\-(). ]+$"),
    files: List[UploadFile] = File(...),
    overwrite: bool = False,
    storage: FileStorageManager = Depends(get_storage_manager)
):
    """📌 다중 PDF 업로드 (최대 10개/요청)"""
    if len(files) > 10:
        raise HTTPException(400, "최대 10개 파일까지 일괄 업로드 가능")

    results = await storage.save_multiple_pdfs(user_id, folder_name, files, overwrite)
    
    return {
        "operation": "batch_upload",
        "user_id": user_id,
        "summary": {
            "success_count": len(results["success"]),
            "failed_count": len(results["failed"])
        },
        "details": results
    }

@router.put("/users/{user_id}/folders/{old_folder}/files/{file_name}/move")
async def move_file(
    user_id: int,
    old_folder: str = Path(..., regex="^[a-zA-Z0-9ㄱ-ㅎ가-힣_\-(). ]+$"),
    file_name: str = Path(..., regex="^[a-zA-Z0-9ㄱ-ㅎ가-힣_\-(). ]+$"),
    new_folder: str = Query(..., regex="^[a-zA-Z0-9ㄱ-ㅎ가-힣_\-(). ]+$"),
    create_if_not_exists: bool = Query(False, description="대상 폴더가 없을 경우 생성 여부"),
    storage: FileStorageManager = Depends(get_storage_manager)
):
    """📌 파일 이동 API"""
    try:
        new_path = storage.move_file(user_id, old_folder, file_name, new_folder, create_if_not_exists)
        return {
            "operation": "move",
            "original_path": f"/storage/{user_id}/{old_folder}/{file_name}",
            "new_path": str(new_path),
            "folder_created": create_if_not_exists,
            "status": "success"
        }
    except FileOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"파일 이동 실패: {str(e)}")
    
@router.put("/users/{user_id}/folders/{folder_name}/files/{file_name}/rename")
async def rename_file(
    user_id: int = Path(...),
    folder_name: str = Path(..., min_length=1, regex="^[a-zA-Z0-9ㄱ-ㅎ가-힣_\-(). ]+$"),
    file_name: str = Path(..., min_length=1, regex="^[a-zA-Z0-9ㄱ-ㅎ가-힣_\-(). ]+$"),
    new_name: str = Query(..., min_length=1, regex="^[a-zA-Z0-9ㄱ-ㅎ가-힣_\-(). ]+$"),
    storage: FileStorageManager = Depends(get_storage_manager)
):
    """📌 파일 이름 변경 (확장자 유지, 중복 시 자동 숫자 추가)"""
    new_path = storage.rename_file(user_id, folder_name, file_name, new_name)

    return {
        "operation": "rename",
        "user_id": user_id,
        "original_name": file_name,
        "new_name": new_path.name,
        "new_path": str(new_path),
        "status": "success"
    }

@router.get(
    "/users/{user_id}/folders",
    summary="사용자 폴더 구조 조회",
    response_model=List[FolderResponse]
)
async def get_user_folders(
    user_id: int = Path(..., description="대상 사용자 ID"),
    include_subfolders: bool = Query(False, description="1단계 하위 폴더 포함 여부"),
    skip: int = Query(0, ge=0, description="페이지네이션 시작 위치"),
    limit: int = Query(100, le=1000, description="한 번에 가져올 최대 폴더 개수"),
    storage: FileStorageManager = Depends(get_storage_manager)
):
    """📌 계층적 폴더 구조 조회 (최대 1단계 하위 폴더 포함 가능)"""
    try:
        return storage.list_folders(user_id, include_subfolders, skip, limit)
    except FileOperationError as e:
        raise HTTPException(status_code=e.code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"폴더 목록 조회 실패: {str(e)}")
    
@router.put("/users/{user_id}/folders/{old_folder}/move",
            summary="폴더 이동",
            description="기존 폴더를 새로운 위치로 이동합니다.")
async def move_folder(
    user_id: int = Path(...),
    old_folder: str = Path(..., min_length=1, regex="^[a-zA-Z0-9ㄱ-ㅎ가-힣_\-(). ]+$"),
    new_folder: str = Path(..., min_length=1, regex="^[a-zA-Z0-9ㄱ-ㅎ가-힣_\-(). ]+$"),
    create_if_not_exists: bool = Query(False, description="대상 폴더가 없을 경우 생성 여부"),
    storage: FileStorageManager = Depends(get_storage_manager)
):
    """📌 폴더 이동 API"""
    try:
        new_path = storage.move_folder(user_id, old_folder, new_folder, create_if_not_exists)
        return {
            "operation": "move_folder",
            "user_id": user_id,
            "original_path": f"/{user_id}/{old_folder}",
            "new_path": str(new_path),
            "folder_created": create_if_not_exists,
            "status": "success"
        }
    except FileOperationError as e:
        raise HTTPException(status_code=400, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"폴더 이동 실패: {str(e)}")
