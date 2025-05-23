from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Path, Query, Body
from typing import List
from sqlalchemy.orm import Session
from app.services.file_service import FileOperationError  # ✅ FileStorageManager 제거
from app.services.pdf_ingest import process_pdf_upload
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
from app.services.point_service import add_points, PointActionType
import logging

router = APIRouter(tags=["PDF Manager"])
logger = logging.getLogger(__name__)

# ✅ 로컬 get_storage_manager 함수 제거 - deps.get_storage_manager만 사용


@router.post(
    "/users/{user_id}/folders/{folder_name}/files",
    response_model=MultiUploadResult,
    summary="PDF 파일 업로드",
    description="지정된 폴더에 PDF 파일을 업로드하고 자동으로 파싱하여 ChromaDB에 저장합니다. S3 또는 로컬 스토리지 사용."
)
async def upload_pdf(
    user_id: int,
    folder_name: str = Path(..., min_length=1, description="업로드할 폴더명"),
    files: List[UploadFile] = File(..., description="업로드할 PDF 파일들"),
    storage = Depends(deps.get_storage_manager),  # ✅ deps에서 가져옴
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """PDF 파일을 업로드하고 자동 파싱 및 임베딩을 수행합니다."""
    try:
        # 권한 확인
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=403, 
                detail="다른 사용자의 폴더에 파일을 업로드할 수 없습니다."
            )

        # S3 또는 로컬 스토리지에 파일 저장
        results = await storage.save_multiple_pdfs(user_id, folder_name, files)

        if len(results["success"]) == 0:
            raise HTTPException(
                status_code=400, 
                detail="업로드에 실패한 파일이 존재합니다."
            )

        # 성공한 파일들에 대해 후속 처리
        for file_info in results["success"]:
            # 포인트 적립
            await add_points(
                db=db,
                user_id=user_id,
                action_type=PointActionType.PDF_UPLOAD,
                description=f"PDF 업로드: {file_info.get('original_name', '파일')}"
            )

            # DB에 파일 정보 기록
            create_pdf_file(
                db=db,
                filename=file_info["saved_name"],
                file_path=file_info["path"],  # S3 URL 또는 로컬 경로
                owner_id=user_id
            )

            # 자동 파싱 및 ChromaDB 저장
            try:
                process_pdf_upload(
                    pdf_path=file_info["path"],  # S3 URL 또는 로컬 경로 처리
                    user_id=str(user_id),
                    folder_name=folder_name
                )
                logger.info(f"PDF 파싱 및 저장 성공: {file_info['path']}")
            except Exception as e:
                logger.error(f"PDF 파싱 실패: {e}")
                # 파싱 실패해도 업로드 자체는 성공으로 처리

        return MultiUploadResult(**results)

    except FileOperationError as e:
        raise HTTPException(status_code=e.code, detail=e.message)
    except Exception as e:
        logger.error(f"PDF 업로드 중 예외 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="파일 업로드 중 오류가 발생했습니다.")


@router.get(
    "/users/{user_id}/folders/{folder_name}/files",
    response_model=List[str],
    summary="폴더 내 파일 목록 조회",
    description="지정된 폴더의 모든 파일 목록을 조회합니다."
)
async def get_files(
    user_id: int = Path(..., description="사용자 ID"),
    folder_name: str = Path(..., description="조회할 폴더명"),
    current_user: User = Depends(deps.get_current_user),
    storage = Depends(deps.get_storage_manager)  # ✅ deps에서 가져옴
):
    """폴더 내 파일 목록을 조회합니다."""
    try:
        # 권한 확인
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=403, 
                detail="다른 사용자의 폴더에 접근할 수 없습니다."
            )
        
        return storage.list_files(user_id, folder_name)
    except FileOperationError as e:
        raise HTTPException(status_code=e.code, detail=e.message)
    except Exception as e:
        logger.error(f"파일 목록 조회 중 예외 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="파일 목록 조회 중 오류가 발생했습니다.")


@router.put(
    "/users/{user_id}/folders/{folder_name}",
    summary="폴더 생성",
    description="새로운 폴더를 생성합니다."
)
async def create_folder(
    user_id: int = Path(..., description="사용자 ID"),
    folder_name: str = Path(..., min_length=1, description="생성할 폴더명"),
    current_user: User = Depends(deps.get_current_user),
    storage = Depends(deps.get_storage_manager)
):
    """새로운 폴더를 생성합니다."""
    try:
        # 권한 확인
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=403, 
                detail="다른 사용자의 폴더를 생성할 수 없습니다."
            )
        
        folder_path = storage.create_folder(user_id, folder_name)
        return {
            "operation": "create_folder",
            "folder_name": folder_name,
            "path": str(folder_path),
            "status": "success"
        }
    except FileOperationError as e:
        raise HTTPException(status_code=e.code, detail=e.message)
    except Exception as e:
        logger.error(f"폴더 생성 중 예외 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="폴더 생성 중 오류가 발생했습니다.")


@router.delete(
    "/users/{user_id}/folders/{folder_name}/files/{file_name}",
    summary="파일 삭제",
    description="지정된 파일을 삭제합니다."
)
async def delete_file(
    user_id: int = Path(..., description="사용자 ID"),
    folder_name: str = Path(..., description="폴더명"),
    file_name: str = Path(..., description="삭제할 파일명"),
    current_user: User = Depends(deps.get_current_user),
    storage = Depends(deps.get_storage_manager)
):
    """지정된 파일을 삭제합니다."""
    try:
        # 권한 확인
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=403, 
                detail="다른 사용자의 파일을 삭제할 수 없습니다."
            )
        
        # S3 또는 로컬에서 파일 삭제
        success = await storage.delete_file(user_id, folder_name, file_name)
        
        if success:
            return {
                "operation": "delete_file",
                "folder_name": folder_name,
                "file_name": file_name,
                "status": "success",
                "message": f"파일 '{file_name}'이 성공적으로 삭제되었습니다."
            }
        else:
            raise HTTPException(status_code=404, detail="파일을 찾을 수 없습니다.")
            
    except FileOperationError as e:
        raise HTTPException(status_code=e.code, detail=e.message)
    except Exception as e:
        logger.error(f"파일 삭제 중 예외 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="파일 삭제 중 오류가 발생했습니다.")


@router.delete(
    "/users/{user_id}/folders/{folder_name}",
    summary="폴더 삭제",
    description="지정된 폴더와 그 안의 모든 파일을 삭제합니다."
)
async def delete_folder(
    user_id: int = Path(..., description="사용자 ID"),
    folder_name: str = Path(..., description="삭제할 폴더명"),
    current_user: User = Depends(deps.get_current_user),
    storage = Depends(deps.get_storage_manager)
):
    """지정된 폴더와 그 안의 모든 파일을 삭제합니다."""
    try:
        # 권한 확인
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=403, 
                detail="다른 사용자의 폴더를 삭제할 수 없습니다."
            )
        
        # S3 또는 로컬에서 폴더 삭제
        storage.delete_folder(user_id, folder_name)
        
        return {
            "operation": "delete_folder",
            "folder_name": folder_name,
            "status": "success",
            "message": f"폴더 '{folder_name}'이 성공적으로 삭제되었습니다."
        }
    except FileOperationError as e:
        raise HTTPException(status_code=e.code, detail=e.message)
    except Exception as e:
        logger.error(f"폴더 삭제 중 예외 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="폴더 삭제 중 오류가 발생했습니다.")


@router.patch(
    "/users/{user_id}/folders/{folder_name}/files/{file_name}/rename",
    response_model=FileRenameResponse,
    summary="파일 이름 변경",
    description="지정된 파일의 이름을 변경합니다."
)
async def rename_file(
    user_id: int = Path(..., description="사용자 ID"),
    folder_name: str = Path(..., description="폴더명"),
    file_name: str = Path(..., description="변경할 파일명"),
    new_name: str = Query(..., min_length=1, description="새로운 파일명"),
    current_user: User = Depends(deps.get_current_user),
    storage = Depends(deps.get_storage_manager)
):
    """파일 이름을 변경합니다."""
    try:
        # 권한 확인
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=403, 
                detail="다른 사용자의 파일 이름을 변경할 수 없습니다."
            )
        
        new_path = storage.rename_file(user_id, folder_name, file_name, new_name)
        return FileRenameResponse(
            operation="rename",
            original_name=file_name,
            new_name=new_name,  # S3에서는 단순히 new_name 사용
            new_path=str(new_path),
            status="success"
        )
    except FileOperationError as e:
        raise HTTPException(status_code=e.code, detail=e.message)
    except Exception as e:
        logger.error(f"파일 이름 변경 중 예외 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="파일 이름 변경 중 오류가 발생했습니다.")


@router.patch(
    "/users/{user_id}/folders/{old_folder}/move",
    response_model=FileMoveResponse,
    summary="폴더 이동",
    description="폴더를 다른 위치로 이동하거나 이름을 변경합니다."
)
async def move_folder(
    user_id: int = Path(..., description="사용자 ID"),
    old_folder: str = Path(..., description="이동할 폴더명"),
    new_folder: str = Query(..., min_length=1, description="새로운 폴더명 또는 경로"),
    create_if_not_exists: bool = Query(False, description="대상 폴더가 없을 때 생성 여부"),
    current_user: User = Depends(deps.get_current_user),
    storage = Depends(deps.get_storage_manager)
):
    """폴더를 이동하거나 이름을 변경합니다."""
    try:
        # 권한 확인
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=403, 
                detail="다른 사용자의 폴더를 이동할 수 없습니다."
            )
        
        new_path = storage.move_folder(user_id, old_folder, new_folder, create_if_not_exists)
        return FileMoveResponse(
            operation="move_folder",
            original_path=f"/{user_id}/{old_folder}",
            new_path=str(new_path),
            folder_created=create_if_not_exists,
            status="success"
        )
    except FileOperationError as e:
        raise HTTPException(status_code=e.code, detail=e.message)
    except Exception as e:
        logger.error(f"폴더 이동 중 예외 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="폴더 이동 중 오류가 발생했습니다.")


@router.patch(
    "/users/{user_id}/folders/{old_folder}/files/{file_name}/move",
    response_model=FileMoveResponse,
    summary="파일 이동",
    description="파일을 다른 폴더로 이동합니다."
)
async def move_file(
    user_id: int = Path(..., description="사용자 ID"),
    old_folder: str = Path(..., description="현재 폴더명"),
    file_name: str = Path(..., description="이동할 파일명"),
    new_folder: str = Query(..., min_length=1, description="이동할 대상 폴더명"),
    create_if_not_exists: bool = Query(False, description="대상 폴더가 없을 때 생성 여부"),
    current_user: User = Depends(deps.get_current_user),
    storage = Depends(deps.get_storage_manager)
):
    """파일을 다른 폴더로 이동합니다."""
    try:
        # 권한 확인
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=403, 
                detail="다른 사용자의 파일을 이동할 수 없습니다."
            )
        
        new_path = storage.move_file(user_id, old_folder, file_name, new_folder, create_if_not_exists)
        return FileMoveResponse(
            operation="move_file",
            original_path=f"/{user_id}/{old_folder}/{file_name}",
            new_path=str(new_path),
            folder_created=create_if_not_exists,
            status="success"
        )
    except FileOperationError as e:
        raise HTTPException(status_code=e.code, detail=e.message)
    except Exception as e:
        logger.error(f"파일 이동 중 예외 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="파일 이동 중 오류가 발생했습니다.")


@router.get(
    "/users/{user_id}/folders",
    response_model=List[FolderResponse],
    summary="사용자 폴더 목록 조회",
    description="사용자의 모든 폴더 구조를 조회합니다."
)
async def list_folders(
    user_id: int = Path(..., description="사용자 ID"),
    include_subfolders: bool = Query(False, description="하위 폴더 포함 여부"),
    skip: int = Query(0, ge=0, description="건너뛸 항목 수"),
    limit: int = Query(100, ge=1, le=1000, description="최대 조회 항목 수"),
    current_user: User = Depends(deps.get_current_user),
    storage = Depends(deps.get_storage_manager)
):
    """사용자의 폴더 구조를 조회합니다."""
    try:
        # 권한 확인
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(
                status_code=403, 
                detail="다른 사용자의 폴더 목록을 조회할 수 없습니다."
            )
        
        return storage.list_folders(user_id, include_subfolders, skip, limit)
    except FileOperationError as e:
        raise HTTPException(status_code=e.code, detail=e.message)
    except Exception as e:
        logger.error(f"폴더 목록 조회 중 예외 발생: {str(e)}")
        raise HTTPException(status_code=500, detail="폴더 목록 조회 중 오류가 발생했습니다.")