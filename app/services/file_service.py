# services/file_service.py

import shutil
import aiofiles
import re
import os
import asyncio
import logging
from uuid import uuid4
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from fastapi import UploadFile
from pydantic import BaseModel


# ==================================================
# 1. 모델 및 예외
# ==================================================
class FolderResponse(BaseModel):
    name: str
    relative_path: str
    created_at: datetime
    subfolders: List[str]


class FileOperationError(Exception):
    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code


class ApiResponse(BaseModel):
    operation: str
    status: str
    message: Optional[str] = None
    original_path: Optional[str] = None
    new_path: Optional[str] = None
    created: Optional[bool] = None


# ==================================================
# 2. FileStorageManager
# ==================================================
class FileStorageManager:
    def __init__(self):
        self.BASE_DIR = Path(os.getenv("STORAGE_PATH", "./storage")).resolve()
        self.BASE_DIR.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------
    # 2.1 유틸리티
    # --------------------------------------------------
    def _sanitize_path(self, user_id: int, *segments: str) -> Path:
        try:
            full_path = self.BASE_DIR.joinpath(str(user_id), *segments).resolve()
            if not str(full_path).startswith(str(self.BASE_DIR)):
                raise ValueError("잘못된 경로 접근 시도")
            return full_path
        except Exception as e:
            raise FileOperationError(str(e), 400)

    def validate_filename(self, name: str) -> bool:
        return bool(re.match(r'^[\wㄱ-ㅎ가-힣\-().&@#%!$ ]+\.[a-zA-Z0-9]+$', name))

    def validate_foldername(self, name: str) -> bool:
        return bool(re.match(r'^[\wㄱ-ㅎ가-힣\-().&@#%!$ ]+$', name))

    def sanitize_filename(self, name: str, default_ext: Optional[str] = None) -> str:
        name = re.sub(r'[^\wㄱ-ㅎ가-힣\-().&@#%!$ ]+', '', name)
        if '.' not in name and default_ext:
            name += f".{default_ext.lstrip('.')}"
        return name.rstrip('.')

    def sanitize_foldername(self, name: str) -> str:
        return re.sub(r'[^\wㄱ-ㅎ가-힣\-().&@#%!$ ]+', '', name)

    def generate_unique_path(self, base_dir: Path, name: str) -> Path:
        new_path = base_dir / name
        count = 1
        stem, ext = os.path.splitext(name)
        while new_path.exists():
            new_path = base_dir / f"{stem}({count}){ext}"
            count += 1
        return new_path

    # --------------------------------------------------
    # 2.2 파일 저장
    # --------------------------------------------------
    async def save_pdf(self, user_id: int, folder: str, file: UploadFile) -> str:
        try:
            if not file.filename.lower().endswith(".pdf"):
                raise FileOperationError("PDF 파일만 허용됩니다.", 400)

            filename = self.sanitize_filename(file.filename, "pdf")
            if not self.validate_filename(filename):
                raise FileOperationError("유효하지 않은 파일명", 400)

            folder_path = self._sanitize_path(user_id, folder)
            folder_path.mkdir(parents=True, exist_ok=True)
            file_path = self.generate_unique_path(folder_path, filename)

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(await file.read())

            return str(file_path)
        except Exception as e:
            raise FileOperationError(f"파일 저장 실패: {e}")

    async def save_multiple_pdfs(self, user_id: int, folder: str, files: List[UploadFile], overwrite: bool = False) -> dict:
        try:
            folder_path = self._sanitize_path(user_id, folder)
            folder_path.mkdir(parents=True, exist_ok=True)

            results = {"total": len(files), "success": [], "failed": []}
            tasks = [self._process_single_file(f, folder_path, overwrite) for f in files]
            file_results = await asyncio.gather(*tasks, return_exceptions=True)

            for r in file_results:
                if isinstance(r, Exception):
                    results["failed"].append(str(r))
                else:
                    results["success"].append(r)

            return results
        except Exception as e:
            raise FileOperationError(f"다중 파일 저장 실패: {e}")

    async def _process_single_file(self, file: UploadFile, folder_path: Path, overwrite: bool) -> dict:
        try:
            if not file.filename.lower().endswith(".pdf"):
                raise FileOperationError(f"{file.filename}: PDF 파일만 허용됩니다.", 400)

            filename = f"{uuid4().hex}_{file.filename}"
            if not self.validate_filename(filename):
                raise FileOperationError(f"{file.filename}: 유효하지 않은 파일명", 400)

            file_path = folder_path / filename
            if file_path.exists() and not overwrite:
                raise FileOperationError(f"{file.filename}: 이미 존재합니다.", 400)

            async with aiofiles.open(file_path, "wb") as f:
                await f.write(await file.read())

            return {
                "original_name": file.filename,
                "saved_name": filename,
                "size": file_path.stat().st_size,
                "path": str(file_path)
            }

        except FileOperationError as e:
            raise e
        except Exception as e:
            raise FileOperationError(f"{file.filename} 처리 실패: {str(e)}", 500)

    # --------------------------------------------------
    # 2.3 파일 관리
    # --------------------------------------------------
    def list_files(self, user_id: int, folder: str, limit: int = 100) -> List[str]:
        try:
            folder_path = self._sanitize_path(user_id, folder)
            if not folder_path.exists() or not folder_path.is_dir():
                raise FileOperationError("폴더를 찾을 수 없습니다.", 404)
            return [f.name for f in folder_path.iterdir() if f.is_file()][:limit]
        except Exception as e:
            raise FileOperationError(f"파일 목록 조회 실패: {e}")

    def delete_file(self, user_id: int, folder: str, filename: str) -> None:
        try:
            file_path = self._sanitize_path(user_id, folder, filename)
            if file_path.exists():
                file_path.unlink()
            else:
                raise FileOperationError("파일이 존재하지 않습니다.", 404)
        except Exception as e:
            raise FileOperationError(f"파일 삭제 실패: {e}")

    def rename_file(self, user_id: int, folder: str, old_name: str, new_name: str) -> Path:
        try:
            # 기존 파일 유효성 체크
            if not self.validate_filename(old_name):
                raise FileOperationError("기존 파일명이 유효하지 않습니다.")

            old_path = self._sanitize_path(user_id, folder, old_name)
            if not old_path.exists():
                raise FileOperationError("기존 파일을 찾을 수 없습니다.")

            # ✅ 기존 확장자 유지
            ext = old_path.suffix
            new_name_with_ext = f"{new_name}{ext}"

            if not self.validate_filename(new_name_with_ext):
                raise FileOperationError("변경할 파일명이 유효하지 않습니다.")

            new_path = self.generate_unique_path(old_path.parent, new_name_with_ext)
            old_path.rename(new_path)

            return new_path

        except Exception as e:
            raise FileOperationError(f"파일 이름 변경 실패: {e}")


    # --------------------------------------------------
    # 2.4 폴더 관리
    # --------------------------------------------------
    def create_folder(self, user_id: int, folder: str) -> Path:
        try:
            folder_path = self._sanitize_path(user_id, folder)
            folder_path.mkdir(parents=True, exist_ok=True)
            return folder_path
        except Exception as e:
            raise FileOperationError(f"폴더 생성 실패: {e}")

    def delete_folder(self, user_id: int, folder: str) -> None:
        try:
            folder_path = self._sanitize_path(user_id, folder)
            shutil.rmtree(folder_path)
        except FileNotFoundError:
            pass
        except Exception as e:
            raise FileOperationError(f"폴더 삭제 실패: {e}")

    def list_folders(self, user_id: int, include_sub: bool = False, skip: int = 0, limit: int = 100) -> List[FolderResponse]:
        try:
            base = self._sanitize_path(user_id)
            if not base.exists():
                return []

            folders = []
            for f in base.iterdir():
                if f.is_dir() and self.validate_foldername(f.name):
                    sub = []
                    if include_sub:
                        sub = [s.name for s in f.iterdir() if s.is_dir()][:100]
                    folders.append(FolderResponse(
                        name=f.name,
                        relative_path=f"/{user_id}/{f.name}",
                        created_at=datetime.fromtimestamp(f.stat().st_ctime),
                        subfolders=sub
                    ))

            return sorted(folders, key=lambda x: x.created_at, reverse=True)[skip:skip + limit]
        except Exception as e:
            raise FileOperationError(f"폴더 목록 조회 실패: {e}")

    def move_folder(self, user_id: int, old: str, new: str, create_if_missing: bool = False) -> Path:
        try:
            old = self.sanitize_foldername(old)
            new = self.sanitize_foldername(new)

            if not (self.validate_foldername(old) and self.validate_foldername(new)):
                raise FileOperationError("유효하지 않은 폴더명")

            old_path = self._sanitize_path(user_id, old)
            new_base = self._sanitize_path(user_id, new)

            if not old_path.exists():
                raise FileOperationError("기존 폴더를 찾을 수 없습니다.")

            if not new_base.exists():
                if create_if_missing:
                    new_base.mkdir(parents=True, exist_ok=True)
                else:
                    raise FileOperationError("대상 폴더가 존재하지 않습니다.")

            new_path = self.generate_unique_path(new_base, old_path.name)
            shutil.move(str(old_path), str(new_path))
            return Path(f"/{user_id}/{new_path.name}")
        except Exception as e:
            raise FileOperationError(f"폴더 이동 실패: {e}")
        
    def move_file(
            self, user_id: int, old_folder: str, filename: str, new_folder: str, create_if_not_exists: bool = False
        ) -> Path:
            """📌 파일 이동 (다른 폴더로)"""
            try:
                old_path = self._sanitize_path(user_id, old_folder, filename)
                if not old_path.exists():
                    raise FileOperationError("원본 파일을 찾을 수 없습니다.", 404)

                new_folder_path = self._sanitize_path(user_id, new_folder)
                if not new_folder_path.exists():
                    if create_if_not_exists:
                        new_folder_path.mkdir(parents=True, exist_ok=True)
                    else:
                        raise FileOperationError("대상 폴더가 존재하지 않습니다.", 404)

                new_path = self.generate_unique_path(new_folder_path, filename)
                shutil.move(str(old_path), str(new_path))
                return new_path
            except Exception as e:
                raise FileOperationError(f"파일 이동 실패: {str(e)}", 500)