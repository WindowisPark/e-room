# app/schemas/file.py

from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime


class FileInfo(BaseModel):
    original_name: str
    saved_name: str
    size: int
    path: str


class MultiUploadResult(BaseModel):
    total: int
    success: List[FileInfo]
    failed: List[str]


class FileRenameResponse(BaseModel):
    operation: str
    original_name: str
    new_name: str
    new_path: str
    status: str


class FileMoveResponse(BaseModel):
    operation: str
    original_path: str
    new_path: str
    folder_created: Optional[bool] = False
    status: str


class FolderResponse(BaseModel):
    name: str
    relative_path: str
    created_at: datetime
    subfolders: List[str]
