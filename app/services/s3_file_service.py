# app/services/s3_file_service.py
import boto3
import logging
import os
from typing import List, Optional, Dict, Any
from fastapi import UploadFile
from botocore.exceptions import ClientError
from app.core.config import settings
from app.schemas.file import FolderResponse
from datetime import datetime
import tempfile

logger = logging.getLogger(__name__)

class S3StorageManager:
    """
    S3 기반 파일 저장 및 관리 서비스
    """

    def __init__(self):
        """S3 클라이언트 초기화"""
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY,
            aws_secret_access_key=settings.AWS_SECRET_KEY,
            region_name=settings.AWS_REGION
        )
        self.bucket_name = settings.S3_BUCKET_NAME

    async def save_pdf(self, user_id: int, folder: str, file: UploadFile) -> str:
        """
        PDF 파일을 S3에 업로드

        Args:
            user_id: 사용자 ID
            folder: 저장할 폴더 경로
            file: 업로드된 파일

        Returns:
            S3 객체 URL
        """
        try:
            if not file.filename.lower().endswith(".pdf"):
                raise ValueError("PDF 파일만 허용됩니다")

            # S3 키 생성 (경로/파일명)
            s3_key = f"users/{user_id}/{folder}/{file.filename}"

            # 파일 데이터 읽기
            file_data = await file.read()

            # S3에 업로드
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_data,
                ContentType='application/pdf'
            )

            # S3 URL 반환
            return f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"

        except Exception as e:
            logger.error(f"S3 파일 업로드 실패: {str(e)}")
            raise

    async def delete_file(self, user_id: int, folder: str, filename: str) -> bool:
        """
        S3에서 파일 삭제

        Args:
            user_id: 사용자 ID
            folder: 폴더 경로
            filename: 파일명

        Returns:
            성공 여부
        """
        try:
            s3_key = f"users/{user_id}/{folder}/{filename}"

            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )

            return True
        except Exception as e:
            logger.error(f"S3 파일 삭제 실패: {str(e)}")
            return False

    def list_files(self, user_id: int, folder: str, limit: int = 100) -> List[str]:
        """
        S3 버킷 내 사용자 폴더의 파일 목록 조회

        Args:
            user_id: 사용자 ID
            folder: 폴더 경로
            limit: 최대 조회 파일 수

        Returns:
            파일명 목록
        """
        try:
            prefix = f"users/{user_id}/{folder}/"

            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=limit
            )

            files = []
            if 'Contents' in response:
                for obj in response['Contents']:
                    # 파일명만 추출 (경로 제외)
                    key = obj['Key']
                    filename = key.replace(prefix, '')
                    if filename:  # 폴더 자체는 제외
                        files.append(filename)

            return files
        except Exception as e:
            logger.error(f"S3 파일 목록 조회 실패: {str(e)}")
            return []
        
    async def save_multiple_pdfs(
        self, user_id: int, folder: str, files: List[UploadFile], overwrite: bool = False
    ) -> Dict[str, Any]:
        """
        여러 개의 PDF 파일을 S3에 업로드

        Args:
            user_id: 사용자 ID
            folder: 저장할 폴더 경로
            files: 업로드된 파일 리스트
            overwrite: 같은 이름일 때 덮어쓸지 여부 (현재는 미사용)

        Returns:
            업로드 결과 dict (성공/실패 내역 포함)
        """
        results = {"total": len(files), "success": [], "failed": []}

        for file in files:
            try:
                if not file.filename.lower().endswith(".pdf"):
                    raise ValueError("PDF 파일만 업로드 가능합니다.")

                s3_key = f"users/{user_id}/{folder}/{file.filename}"
                file_data = await file.read()

                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    Body=file_data,
                    ContentType="application/pdf"
                )

                results["success"].append({
                    "original_name": file.filename,
                    "saved_name": file.filename,
                    "size": len(file_data),
                    "path": f"https://{self.bucket_name}.s3.amazonaws.com/{s3_key}"
                })
            except Exception as e:
                logger.error(f"파일 업로드 실패: {file.filename} - {str(e)}")
                results["failed"].append(f"{file.filename}: {str(e)}")

        return results
    
    def list_folders(self, user_id: int, include_subfolders: bool = False, skip: int = 0, limit: int = 100) -> List[FolderResponse]:
        try:
            prefix = f"users/{user_id}/"

            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                Delimiter="/",
                MaxKeys=limit + skip
            )

            folders = []
            for entry in response.get("CommonPrefixes", [])[skip:skip + limit]:
                full_prefix = entry["Prefix"]
                folder_name = full_prefix[len(prefix):].strip("/")
                folders.append(FolderResponse(
                    name=folder_name,
                    relative_path=f"/{user_id}/{folder_name}",
                    created_at=datetime.now(),  # 현재 시간으로 채움
                    subfolders=[]  # S3에서는 미지원이므로 비워둠
                ))

            return folders

        except Exception as e:
            logger.error(f"S3 폴더 목록 조회 실패: {str(e)}")
            return []
        
    def create_folder(self, user_id: int, folder: str) -> str:
        """
        S3에 '폴더' 생성 (빈 객체를 업로드하여 prefix 생성)

        Args:
            user_id: 사용자 ID
            folder: 생성할 폴더명

        Returns:
            S3 경로 문자열
        """
        try:
            prefix = f"users/{user_id}/{folder}/"
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=prefix  # 폴더처럼 인식될 prefix
            )
            return f"s3://{self.bucket_name}/{prefix}"
        except Exception as e:
            logger.error(f"S3 폴더 생성 실패: {str(e)}")
            raise

    def delete_folder(self, user_id: int, folder: str) -> None:
        """
        S3에서 폴더(접두어 prefix 전체)를 삭제
        """
        prefix = f"users/{user_id}/{folder}/"
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            if 'Contents' in response:
                objects = [{'Key': obj['Key']} for obj in response['Contents']]
                self.s3_client.delete_objects(
                    Bucket=self.bucket_name,
                    Delete={'Objects': objects}
                )
        except Exception as e:
            logger.error(f"S3 폴더 삭제 실패: {str(e)}")
            raise

    def rename_file(self, user_id: int, folder: str, old_name: str, new_name: str) -> str:
        """
        S3 파일 이름 변경 (실제로는 복사 후 원본 삭제)
        """
        old_key = f"users/{user_id}/{folder}/{old_name}"
        new_key = f"users/{user_id}/{folder}/{new_name}"
        try:
            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                CopySource={'Bucket': self.bucket_name, 'Key': old_key},
                Key=new_key
            )
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=old_key)
            return f"https://{self.bucket_name}.s3.amazonaws.com/{new_key}"
        except Exception as e:
            logger.error(f"S3 파일 이름 변경 실패: {str(e)}")
            raise

    def move_file(self, user_id: int, old_folder: str, filename: str, new_folder: str, create_if_not_exists: bool = False) -> str:
        """
        S3 파일 이동 (실제로는 복사 후 삭제)
        """
        old_key = f"users/{user_id}/{old_folder}/{filename}"
        new_key = f"users/{user_id}/{new_folder}/{filename}"
        try:
            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                CopySource={'Bucket': self.bucket_name, 'Key': old_key},
                Key=new_key
            )
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=old_key)
            return f"https://{self.bucket_name}.s3.amazonaws.com/{new_key}"
        except Exception as e:
            logger.error(f"S3 파일 이동 실패: {str(e)}")
            raise

    def move_folder(self, user_id: int, old_folder: str, new_folder: str, create_if_not_exists: bool = False) -> str:
        """
        S3 폴더 이동 (모든 파일을 복사 후 삭제)
        """
        old_prefix = f"users/{user_id}/{old_folder}/"
        new_prefix = f"users/{user_id}/{new_folder}/"
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=old_prefix)
            if 'Contents' not in response:
                raise ValueError("이동할 폴더에 파일이 없습니다.")

            for obj in response['Contents']:
                old_key = obj['Key']
                new_key = old_key.replace(old_prefix, new_prefix, 1)
                self.s3_client.copy_object(
                    Bucket=self.bucket_name,
                    CopySource={'Bucket': self.bucket_name, 'Key': old_key},
                    Key=new_key
                )
            # 이후 원본 삭제
            self.delete_folder(user_id, old_folder)
            return f"s3://{self.bucket_name}/{new_prefix}"
        except Exception as e:
            logger.error(f"S3 폴더 이동 실패: {str(e)}")
            raise

    def download_to_tempfile(self, s3_key: str) -> str:
        """
        S3에서 PDF 파일을 로컬 임시 파일로 다운로드하고 경로 반환

        Args:
            s3_key: S3 내부 객체 경로 (예: users/2/정보보호/sample.pdf)

        Returns:
            로컬 임시 파일 경로 (str)
        """
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                self.s3_client.download_fileobj(self.bucket_name, s3_key, tmp)
                logger.info(f"📥 S3 -> Temp 다운로드 완료: {s3_key} -> {tmp.name}")
                return tmp.name
        except Exception as e:
            logger.error(f"S3 파일 다운로드 실패: {str(e)}")
            raise
