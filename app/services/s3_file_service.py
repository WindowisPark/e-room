# app/services/s3_file_service.py
import boto3
import logging
import os
from typing import List, Optional, Dict, Any
from fastapi import UploadFile
from botocore.exceptions import ClientError
from app.core.config import settings

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