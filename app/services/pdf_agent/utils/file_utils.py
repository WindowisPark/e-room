# app/services/pdf_agent/utils/file_utils.py

import os
import json
from datetime import datetime
from typing import Tuple, Optional

def get_timestamp_filename(task_type: str, extension: str) -> str:
    """
    타임스탬프 기반 파일명 생성
    
    Args:
        task_type: "summary", "exam", "schedule"
        extension: "md", "json"
    
    Returns:
        "summary_20250526_143022.md" 형식의 파일명
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{task_type}_{timestamp}.{extension}"

def save_output_file(
    user_id: str, 
    task_type: str, 
    content: str, 
    file_format: str = "md"
) -> Tuple[str, str]:
    """
    일관된 형식으로 결과 파일 저장
    
    Args:
        user_id: 사용자 ID
        task_type: "summary", "exam", "schedule"
        content: 저장할 내용 (문자열 또는 JSON)
        file_format: "md" 또는 "json"
    
    Returns:
        (파일 전체 경로, 파일명) 튜플
    """
    # 디렉토리 생성
    output_dir = f"{user_id}/{task_type}"
    os.makedirs(output_dir, exist_ok=True)
    
    # 파일명 생성
    filename = get_timestamp_filename(task_type, file_format)
    file_path = os.path.join(output_dir, filename)
    
    # 파일 저장
    try:
        if file_format == "json":
            # JSON 형식으로 저장
            if isinstance(content, str):
                # 문자열이면 JSON 파싱 시도
                try:
                    content_dict = json.loads(content)
                except json.JSONDecodeError:
                    # 파싱 실패시 원본 문자열을 content 키에 저장
                    content_dict = {"content": content}
            else:
                content_dict = content
                
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(content_dict, f, ensure_ascii=False, indent=2)
        else:
            # Markdown 또는 텍스트로 저장
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(str(content))
                
        return file_path, filename
        
    except Exception as e:
        raise Exception(f"파일 저장 실패: {str(e)}")

def get_file_info(file_path: str) -> dict:
    """
    파일 정보 반환
    
    Args:
        file_path: 파일 경로
        
    Returns:
        파일 정보 딕셔너리
    """
    if not os.path.exists(file_path):
        return {}
        
    try:
        stat = os.stat(file_path)
        filename = os.path.basename(file_path)
        extension = filename.split('.')[-1] if '.' in filename else ''
        
        return {
            "path": file_path,
            "filename": filename,
            "size": stat.st_size,
            "format": "json" if extension == "json" else "markdown",
            "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
    except Exception:
        return {"path": file_path, "filename": os.path.basename(file_path)}

def cleanup_old_files(user_id: str, task_type: str, keep_count: int = 10) -> int:
    """
    오래된 파일들 정리 (최신 N개만 유지)
    
    Args:
        user_id: 사용자 ID
        task_type: "summary", "exam", "schedule"
        keep_count: 유지할 파일 개수
        
    Returns:
        삭제된 파일 개수
    """
    output_dir = f"{user_id}/{task_type}"
    
    if not os.path.exists(output_dir):
        return 0
        
    try:
        # 파일 목록을 수정 시간 기준으로 정렬
        files = []
        for filename in os.listdir(output_dir):
            file_path = os.path.join(output_dir, filename)
            if os.path.isfile(file_path):
                files.append((file_path, os.path.getmtime(file_path)))
        
        # 수정 시간 기준 내림차순 정렬 (최신 파일이 먼저)
        files.sort(key=lambda x: x[1], reverse=True)
        
        # 오래된 파일 삭제
        deleted_count = 0
        for file_path, _ in files[keep_count:]:
            try:
                os.remove(file_path)
                deleted_count += 1
            except Exception:
                pass
                
        return deleted_count
        
    except Exception:
        return 0