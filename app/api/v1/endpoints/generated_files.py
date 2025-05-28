
# ===== 1. app/api/v1/endpoints/generated_files.py (새 파일 생성) =====

import os
import json
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Path, Query
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from app.api import deps
from app.models.user import User

logger = logging.getLogger(__name__)
router = APIRouter()

class GeneratedFileService:
    """생성된 파일 관리 서비스"""
    
    BASE_STORAGE_PATH = "storage"
    ALLOWED_FILE_TYPES = ["summary", "exam", "schedule"]
    
    @staticmethod
    def get_user_storage_path(user_id: int, file_type: str = None) -> str:
        """사용자별 저장소 경로 반환"""
        if file_type:
            return os.path.join(GeneratedFileService.BASE_STORAGE_PATH, str(user_id), file_type)
        return os.path.join(GeneratedFileService.BASE_STORAGE_PATH, str(user_id))
    
    @staticmethod
    def validate_file_type(file_type: str) -> bool:
        """파일 타입 유효성 검증"""
        return file_type in GeneratedFileService.ALLOWED_FILE_TYPES
    
    @staticmethod
    def get_file_path(user_id: int, file_type: str, filename: str) -> str:
        """전체 파일 경로 반환"""
        return os.path.join(
            GeneratedFileService.get_user_storage_path(user_id, file_type),
            filename
        )


# ===== 파일 내용 조회 API =====
@router.get("/{user_id}/{file_type}/{filename}")
async def get_file_content(
    user_id: int = Path(..., description="사용자 ID"),
    file_type: str = Path(..., description="파일 타입 (summary/exam/schedule)"),
    filename: str = Path(..., description="파일명"),
    current_user: User = Depends(deps.get_current_user)
):
    """
    생성된 파일 내용 조회
    - summary/exam: 마크다운 텍스트 반환
    - schedule: JSON 데이터 반환
    """
    try:
        # 권한 확인
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="다른 사용자의 파일에 접근할 수 없습니다.")
        
        # 파일 타입 검증
        if not GeneratedFileService.validate_file_type(file_type):
            raise HTTPException(
                status_code=400, 
                detail=f"지원하지 않는 파일 타입입니다. 허용 타입: {GeneratedFileService.ALLOWED_FILE_TYPES}"
            )
        
        # 파일 경로 확인
        file_path = GeneratedFileService.get_file_path(user_id, file_type, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {filename}")
        
        # 파일 메타데이터
        file_stat = os.stat(file_path)
        
        # 타입별 특화 처리
        if file_type == "schedule":
            return await _handle_schedule_file(file_path, filename, file_stat)
        else:  # summary, exam
            return await _handle_markdown_file(file_path, filename, file_type, file_stat)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 내용 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="파일 조회 중 오류가 발생했습니다.")


# ===== 파일 다운로드 API =====
@router.get("/{user_id}/{file_type}/{filename}/download")
async def download_file(
    user_id: int = Path(..., description="사용자 ID"),
    file_type: str = Path(..., description="파일 타입 (summary/exam/schedule)"),
    filename: str = Path(..., description="파일명"),
    current_user: User = Depends(deps.get_current_user)
):
    """생성된 파일 다운로드"""
    try:
        # 권한 확인
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="다른 사용자의 파일을 다운로드할 수 없습니다.")
        
        # 파일 타입 검증
        if not GeneratedFileService.validate_file_type(file_type):
            raise HTTPException(status_code=400, detail="지원하지 않는 파일 타입입니다.")
        
        # 파일 경로 확인
        file_path = GeneratedFileService.get_file_path(user_id, file_type, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"다운로드할 파일을 찾을 수 없습니다: {filename}")
        
        # 파일 확장자별 MIME 타입 설정
        if filename.endswith('.md'):
            media_type = 'text/markdown'
        elif filename.endswith('.json'):
            media_type = 'application/json'
        else:
            media_type = 'text/plain'
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=filename,
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 다운로드 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="파일 다운로드 중 오류가 발생했습니다.")


# ===== 파일 목록 조회 API =====
@router.get("/{user_id}/{file_type}")
async def list_files(
    user_id: int = Path(..., description="사용자 ID"),
    file_type: str = Path(..., description="파일 타입 (summary/exam/schedule)"),
    limit: int = Query(20, ge=1, le=100, description="최대 조회 개수"),
    offset: int = Query(0, ge=0, description="건너뛸 개수"),
    sort_by: str = Query("created_desc", description="정렬 방식 (created_desc/created_asc/name_asc/name_desc)"),
    current_user: User = Depends(deps.get_current_user)
):
    """사용자의 생성된 파일 목록 조회"""
    try:
        # 권한 확인
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="다른 사용자의 파일 목록을 조회할 수 없습니다.")
        
        # 파일 타입 검증
        if not GeneratedFileService.validate_file_type(file_type):
            raise HTTPException(status_code=400, detail="지원하지 않는 파일 타입입니다.")
        
        # 디렉토리 확인
        directory = GeneratedFileService.get_user_storage_path(user_id, file_type)
        
        if not os.path.exists(directory):
            return {
                "files": [],
                "total": 0,
                "file_type": file_type,
                "pagination": {
                    "limit": limit,
                    "offset": offset,
                    "has_more": False
                }
            }
        
        # 파일 목록 수집
        files = []
        for filename in os.listdir(directory):
            file_path = os.path.join(directory, filename)
            
            if os.path.isfile(file_path):
                file_stat = os.stat(file_path)
                
                files.append({
                    "filename": filename,
                    "size": file_stat.st_size,
                    "size_human": _format_file_size(file_stat.st_size),
                    "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                    "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                    "file_type": file_type,
                    "download_url": f"/api/v1/files/{user_id}/{file_type}/{filename}/download"
                })
        
        # 정렬 처리
        if sort_by == "created_desc":
            files.sort(key=lambda x: x["created_at"], reverse=True)
        elif sort_by == "created_asc":
            files.sort(key=lambda x: x["created_at"])
        elif sort_by == "name_asc":
            files.sort(key=lambda x: x["filename"])
        elif sort_by == "name_desc":
            files.sort(key=lambda x: x["filename"], reverse=True)
        
        # 페이징 처리
        total = len(files)
        paginated_files = files[offset:offset + limit]
        
        return {
            "files": paginated_files,
            "total": total,
            "file_type": file_type,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 목록 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="파일 목록 조회 중 오류가 발생했습니다.")


# ===== 파일 삭제 API =====
@router.delete("/{user_id}/{file_type}/{filename}")
async def delete_file(
    user_id: int = Path(..., description="사용자 ID"),
    file_type: str = Path(..., description="파일 타입 (summary/exam/schedule)"),
    filename: str = Path(..., description="파일명"),
    current_user: User = Depends(deps.get_current_user)
):
    """생성된 파일 삭제"""
    try:
        # 권한 확인
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="다른 사용자의 파일을 삭제할 수 없습니다.")
        
        # 파일 타입 검증
        if not GeneratedFileService.validate_file_type(file_type):
            raise HTTPException(status_code=400, detail="지원하지 않는 파일 타입입니다.")
        
        # 파일 경로 확인
        file_path = GeneratedFileService.get_file_path(user_id, file_type, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"삭제할 파일을 찾을 수 없습니다: {filename}")
        
        # 파일 삭제
        os.remove(file_path)
        
        logger.info(f"파일 삭제 완료: user_id={user_id}, file_type={file_type}, filename={filename}")
        
        return {
            "success": True,
            "message": f"파일이 성공적으로 삭제되었습니다: {filename}",
            "deleted_file": {
                "filename": filename,
                "file_type": file_type,
                "deleted_at": datetime.now().isoformat()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 삭제 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="파일 삭제 중 오류가 발생했습니다.")


# ===== 전체 파일 통계 API =====
@router.get("/{user_id}/stats")
async def get_file_stats(
    user_id: int = Path(..., description="사용자 ID"),
    current_user: User = Depends(deps.get_current_user)
):
    """사용자의 생성된 파일 통계"""
    try:
        # 권한 확인
        if current_user.id != user_id and not current_user.is_admin:
            raise HTTPException(status_code=403, detail="다른 사용자의 통계를 조회할 수 없습니다.")
        
        stats = {
            "user_id": user_id,
            "summary": {"count": 0, "total_size": 0, "latest_file": None},
            "exam": {"count": 0, "total_size": 0, "latest_file": None},
            "schedule": {"count": 0, "total_size": 0, "latest_file": None},
            "total_files": 0,
            "total_size": 0,
            "total_size_human": "0 B"
        }
        
        for file_type in GeneratedFileService.ALLOWED_FILE_TYPES:
            directory = GeneratedFileService.get_user_storage_path(user_id, file_type)
            
            if os.path.exists(directory):
                files = []
                total_size = 0
                
                for filename in os.listdir(directory):
                    file_path = os.path.join(directory, filename)
                    if os.path.isfile(file_path):
                        file_stat = os.stat(file_path)
                        total_size += file_stat.st_size
                        
                        files.append({
                            "filename": filename,
                            "created_at": datetime.fromtimestamp(file_stat.st_ctime)
                        })
                
                # 최신 파일 찾기
                latest_file = None
                if files:
                    latest_file = max(files, key=lambda x: x["created_at"])
                    latest_file["created_at"] = latest_file["created_at"].isoformat()
                
                stats[file_type] = {
                    "count": len(files),
                    "total_size": total_size,
                    "total_size_human": _format_file_size(total_size),
                    "latest_file": latest_file
                }
                
                stats["total_files"] += len(files)
                stats["total_size"] += total_size
        
        stats["total_size_human"] = _format_file_size(stats["total_size"])
        
        return stats
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"파일 통계 조회 실패: {str(e)}")
        raise HTTPException(status_code=500, detail="파일 통계 조회 중 오류가 발생했습니다.")


# ===== 헬퍼 함수들 =====

async def _handle_schedule_file(file_path: str, filename: str, file_stat) -> Dict[str, Any]:
    """스케줄 JSON 파일 특화 처리"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            schedule_data = json.load(f)
        
        # 스케줄 분석
        total_days = len(schedule_data)
        subjects = set()
        total_study_hours = 0
        
        for day_plan in schedule_data.values():
            if isinstance(day_plan, dict):
                subjects.update(day_plan.keys())
                for subject_plan in day_plan.values():
                    if isinstance(subject_plan, dict) and "예상 학습 시간" in subject_plan:
                        time_str = subject_plan["예상 학습 시간"]
                        # "2시간" 형태에서 숫자 추출
                        try:
                            hours = int(''.join(filter(str.isdigit, time_str)))
                            total_study_hours += hours
                        except:
                            pass
        
        return {
            "success": True,
            "file_type": "schedule",
            "content_type": "application/json",
            "filename": filename,
            "data": schedule_data,
            "metadata": {
                "total_days": total_days,
                "subjects": list(subjects),
                "subject_count": len(subjects),
                "total_study_hours": total_study_hours,
                "file_size": file_stat.st_size,
                "file_size_human": _format_file_size(file_stat.st_size),
                "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            }
        }
        
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="스케줄 파일 형식이 올바르지 않습니다.")


async def _handle_markdown_file(file_path: str, filename: str, file_type: str, file_stat) -> Dict[str, Any]:
    """마크다운 파일 특화 처리"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 마크다운 분석
        lines = content.split('\n')
        sections = [line for line in lines if line.startswith('## ')]
        
        # 단어 수 계산
        word_count = len(content.split())
        
        return {
            "success": True,
            "file_type": file_type,
            "content_type": "text/markdown",
            "filename": filename,
            "content": content,
            "metadata": {
                "total_sections": len(sections),
                "sections": sections,
                "line_count": len(lines),
                "word_count": word_count,
                "character_count": len(content),
                "file_size": file_stat.st_size,
                "file_size_human": _format_file_size(file_stat.st_size),
                "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat()
            }
        }
        
    except UnicodeDecodeError:
        raise HTTPException(status_code=500, detail="파일 인코딩 오류입니다.")


def _format_file_size(size_bytes: int) -> str:
    """파일 크기를 사람이 읽기 쉬운 형태로 변환"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    size = float(size_bytes)
    
    while size >= 1024.0 and i < len(size_names) - 1:
        size /= 1024.0
        i += 1
    
    return f"{size:.1f} {size_names[i]}"