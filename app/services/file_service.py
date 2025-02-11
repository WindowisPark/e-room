import shutil
import aiofiles
import re
from uuid import uuid4
from pathlib import Path
from fastapi import HTTPException, UploadFile
from typing import List, Optional
import os
import asyncio
from datetime import datetime
from pydantic import BaseModel
from itertools import islice


# ==================================================
# 1. 데이터 모델 및 예외 클래스
# ==================================================
class FolderResponse(BaseModel):
    """📌 폴더 정보 응답 모델"""
    name: str
    relative_path: str
    created_at: datetime
    subfolders: List[str]


class FileOperationError(Exception):
    """📌 파일 조작 관련 예외 클래스"""
    def __init__(self, message: str, code: int = 500):
        self.message = message
        self.code = code

class ApiResponse(BaseModel):
    """📌 표준 API 응답 모델"""
    operation: str
    status: str
    message: Optional[str] = None
    original_path: Optional[str] = None
    new_path: Optional[str] = None
    created: Optional[bool] = None


# ==================================================
# 2. 파일 저장 및 관리 클래스
# ==================================================
class FileStorageManager:
    """📂 파일 저장 및 관리 클래스"""

    def __init__(self):
        """📌 초기화: 기본 저장 경로 설정"""
        self.BASE_DIR = Path(os.getenv("STORAGE_PATH", "./storage")).resolve()
        self.BASE_DIR.mkdir(parents=True, exist_ok=True)

    # ==================================================
    # 2.1 유틸리티 메서드
    # ==================================================
    def _sanitize_path(self, user_id: int, *path_segments) -> Path:
        """📌 경로 보안 검증 및 생성"""
        try:
            user_id_str = str(user_id)
            full_path = self.BASE_DIR.joinpath(user_id_str, *path_segments).resolve()

            # 보안 검증: BASE_DIR 내에서만 허용
            if not str(full_path).startswith(str(self.BASE_DIR)):
                raise ValueError("잘못된 경로 접근 시도")

            return full_path
        except Exception as e:
            raise FileOperationError(str(e), 400)

    @staticmethod
    def _validate_name(name: str, is_file: bool = True) -> bool:
        """📌 파일/폴더명 유효성 검사"""
        pattern = r'^[a-zA-Z0-9ㄱ-ㅎ가-힣_\-().&@#%!$ ]+$'
        if is_file:
            pattern = r'^[a-zA-Z0-9ㄱ-ㅎ가-힣_\-().&@#%!$ ]+\.[a-zA-Z0-9]+$' 

        return bool(re.match(pattern, name))

    @staticmethod
    def _sanitize_name(name: str, is_file: bool = True) -> str:
        """📌 유효하지 않은 문자 자동 변환"""
        sanitized = re.sub(r'[^a-zA-Z0-9ㄱ-ㅎ가-힣_\-().&@#%!$ ]+', '', name)
        if is_file and '.' not in sanitized:
            sanitized += ".pdf"  # 확장자 자동 추가
        return sanitized.rstrip('.')  # 끝에 . 남지 않도록 정리

    def generate_unique_name(self, folder: Path, name: str) -> Path:
        """📌 동일한 이름이 존재하면 (1), (2) 숫자 추가"""
        new_path = folder / name
        count = 1
        while new_path.exists():
            file_stem, file_ext = os.path.splitext(name)
            new_path = folder / f"{file_stem}({count}){file_ext}"
            count += 1
        return new_path

    # ==================================================
    # 2.2 파일 업로드 관련 메서드
    # ==================================================
    async def save_pdf(self, user_id: int, folder_name: str, file: UploadFile) -> str:
        """📌 PDF 파일 저장"""
        try:
            if not file.filename.lower().endswith(".pdf"):
                raise FileOperationError("PDF 파일만 업로드 가능합니다.", 400)

            # ✅ 파일명 자동 정리
            filename = self._sanitize_name(file.filename)
            if not self._validate_name(filename):
                raise FileOperationError(f"잘못된 문자가 포함된 파일명: {filename}")

            # ✅ 경로 생성
            folder_path = self._sanitize_path(user_id, folder_name)
            folder_path.mkdir(parents=True, exist_ok=True)

            # ✅ 중복 파일명 방지
            file_path = self.generate_unique_name(folder_path, filename)

            async with aiofiles.open(file_path, "wb") as buffer:
                await buffer.write(await file.read())

            return str(file_path)

        except Exception as e:
            raise FileOperationError(f"파일 저장 실패: {str(e)}")

    async def save_multiple_pdfs(
        self,
        user_id: int,
        folder_name: str,
        files: List[UploadFile],
        overwrite: bool = False
    ) -> dict:
        """📌 여러 PDF 파일 일괄 저장 (병렬 처리)"""
        try:
            user_id_str = str(user_id)
            if not all(self._validate_name(n) for n in [user_id_str, folder_name]):
                raise FileOperationError("잘못된 문자가 포함된 이름")

            folder_path = self._sanitize_path(user_id, folder_name)
            folder_path.mkdir(parents=True, exist_ok=True)

            results = {
                "total": len(files),
                "success": [],
                "failed": []
            }

            # 병렬 처리 코루틴 생성
            tasks = [self._process_single_file(f, folder_path, overwrite) for f in files]
            file_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in file_results:
                if isinstance(result, Exception):
                    results["failed"].append(str(result))
                else:
                    results["success"].append(result)

            return results

        except FileOperationError as e:
            raise e
        except Exception as e:
            raise FileOperationError(f"일괄 업로드 실패: {str(e)}")

    async def _process_single_file(
        self,
        file: UploadFile,
        folder_path: Path,
        overwrite: bool
    ) -> dict:
        """📌 개별 파일 처리 코루틴"""
        try:
            # 확장자 검증
            if not file.filename.lower().endswith(".pdf"):
                raise ValueError(f"'{file.filename}': PDF 파일만 허용됩니다")

            # 파일명 생성
            filename = f"{uuid4().hex}_{file.filename}"
            if not self._validate_name(filename):
                raise ValueError(f"'{file.filename}': 유효하지 않은 파일명")

            file_path = folder_path / filename

            # 덮어쓰기 방지
            if file_path.exists() and not overwrite:
                raise ValueError(f"'{file.filename}': 동일한 파일명 존재")

            # 비동기 저장
            async with aiofiles.open(file_path, "wb") as buffer:
                await buffer.write(await file.read())

            return {
                "original_name": file.filename,
                "saved_name": filename,
                "size": file_path.stat().st_size,
                "path": str(file_path)
            }

        except Exception as e:
            raise e

    # ==================================================
    # 2.3 파일 관리 메서드
    # ==================================================
    # app/services/file_service.py

    def list_files(self, user_id: int, folder_name: str, limit: int = 100) -> List[str]:
        """📌 파일 목록 조회 (최대 100개 제한)"""
        try:
            folder_path = self._sanitize_path(user_id, folder_name)
            
            if not folder_path.exists():
                raise FileOperationError(f"폴더 '{folder_name}'을 찾을 수 없습니다.", 404)

            if not folder_path.is_dir():
                raise FileOperationError(f"'{folder_name}'은 폴더가 아닙니다.", 400)

            # ✅ 최대 100개의 파일만 반환 (과부하 방지)
            files = [f.name for f in folder_path.iterdir() if f.is_file()][:limit]

            # ✅ 디버깅 로그 추가
            print(f"[DEBUG] '{folder_name}' 폴더 내 파일 개수: {len(files)}")

            return files

        except FileOperationError as e:
            raise e
        except Exception as e:
            raise FileOperationError(f"파일 목록 조회 실패: {str(e)}", 500)    


    def delete_file(self, user_id: int, folder_name: str, filename: str) -> None:
        """📌 파일 삭제"""
        try:
            file_path = self._sanitize_path(user_id, folder_name, filename)
            if file_path.exists():
                file_path.unlink()
            else:
                raise FileOperationError("파일을 찾을 수 없습니다.", 404)
        except FileOperationError as e:
            raise e
        except Exception as e:
            raise FileOperationError(str(e), 500)

    def rename_file(self, user_id: int, folder_name: str, file_name: str, new_name: str) -> Path:
        """📌 파일 이름 변경"""
        try:
            if not self._validate_name(file_name) or not self._validate_name(new_name):
                raise FileOperationError("유효하지 않은 파일명")

            # 기존 파일 경로
            old_path = self._sanitize_path(user_id, folder_name, file_name)
            if not old_path.exists():
                raise FileOperationError("파일을 찾을 수 없습니다.")

            # 확장자는 유지
            file_ext = old_path.suffix
            new_name_with_ext = f"{new_name}{file_ext}"

            # 중복 처리
            new_path = self.generate_unique_filename(old_path.parent, new_name_with_ext)

            # 파일명 변경
            old_path.rename(new_path)

            return new_path

        except FileOperationError as e:
            raise e
        except Exception as e:
            raise FileOperationError(f"파일 이름 변경 실패: {str(e)}")

    # ==================================================
    # 2.4 폴더 관리 메서드
    # ==================================================
    def create_folder(self, user_id: int, folder_name: str) -> Path:
        """📌 폴더 생성 (멱등성 유지)"""
        try:
            folder_path = self._sanitize_path(user_id, folder_name)
            folder_path.mkdir(parents=True, exist_ok=True)
            return folder_path
        except Exception as e:
            raise FileOperationError(f"폴더 생성 실패: {str(e)}", 400)

    def delete_folder(self, user_id: int, folder_name: str) -> None:
        """📌 폴더 삭제 (재귀적 삭제)"""
        try:
            folder_path = self._sanitize_path(user_id, folder_name)
            if folder_path.exists():
                shutil.rmtree(folder_path)
        except FileNotFoundError:
            pass  # 이미 삭제된 경우 무시
        except Exception as e:
            raise FileOperationError(str(e), 500)

    def list_folders(
        self, user_id: int, include_subfolders: bool = False, skip: int = 0, limit: int = 100
    ) -> List[FolderResponse]:
        """📌 사용자 폴더 목록 조회"""
        try:
            user_path = self._sanitize_path(user_id)
            print(f"[DEBUG] User path: {user_path}")  # 실제 환경에선 logging 사용

            if not user_path.exists():
                print(f"[DEBUG] User folder does not exist: {user_path}")
                return []

            folders = []
            for folder in user_path.iterdir():
                print(f"[DEBUG] Processing folder: {folder}")
                if folder.is_dir() and self._validate_name(folder.name, is_file=False):
                    folder_info = FolderResponse(
                        name=folder.name,
                        relative_path=f"/{user_id}/{folder.name}",
                        created_at=datetime.fromtimestamp(folder.stat().st_ctime),
                        subfolders=[]
                    )

                    if include_subfolders:
                        subfolders = [
                            sub.name for sub in folder.iterdir()
                            if sub.is_dir() and self._validate_name(sub.name, is_file=False)
                        ][:100]
                        folder_info.subfolders = subfolders

                    folders.append(folder_info)

            return sorted(folders, key=lambda x: x.created_at, reverse=True)[skip:skip + limit]

        except Exception as e:
            print(f"[ERROR] Failed to list folders: {str(e)}")
            raise FileOperationError(f"폴더 목록 조회 실패: {str(e)}", 500)
        
    def generate_unique_foldername(self, folder: Path) -> Path:   
        """📌 중복 폴더 처리: `(1)`, `(2)` 추가"""
        new_path = folder
        count = 1
        while new_path.exists():
            new_path = folder.parent / f"{folder.name}({count})"
            count += 1
        return new_path    

    def move_folder(
        self, user_id: int, old_folder: str, new_folder: str, create_if_not_exists: bool = False
    ) -> Path:
        """📌 폴더 이동 기능 개선"""
        try:
            old_folder = self._sanitize_name(old_folder, is_file=False)
            new_folder = self._sanitize_name(new_folder, is_file=False)

            if not self._validate_foldername(old_folder) or not self._validate_foldername(new_folder):
                raise FileOperationError("유효하지 않은 폴더명")

            # 기존 폴더 확인
            old_path = self._sanitize_path(user_id, old_folder)
            if not old_path.exists():
                raise FileOperationError("폴더를 찾을 수 없습니다.")

            # 새로운 폴더 경로 생성
            new_folder_path = self._sanitize_path(user_id, new_folder)

            # 폴더 자동 생성 여부 체크
            if not new_folder_path.exists():
                if create_if_not_exists:
                    new_folder_path.mkdir(parents=True, exist_ok=True)
                else:
                    raise FileOperationError("대상 폴더가 존재하지 않습니다.")

            # 같은 폴더명이 존재하는 경우 `(1)`, `(2)` 숫자 붙이기
            new_path = self.generate_unique_name(new_folder_path, old_path.name)

            # 폴더 이동
            shutil.move(str(old_path), str(new_path))

            return Path(f"/{user_id}/{new_path.name}")  # ✅ 상대 경로 반환

        except FileOperationError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"폴더 이동 실패: {str(e)}")   