# app/services/pdf_agent/embedding_service.py
"""
PDF 문서용 벡터 임베딩 서비스.
pgvector를 사용하여 문서 임베딩의 생성 및 검색을 처리합니다.
"""

import logging
import asyncio
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from sqlalchemy.orm import Session
from sqlalchemy import text
from openai import OpenAI, AsyncOpenAI

from app.core.config import settings

logger = logging.getLogger(__name__)

class EmbeddingService:
    """
    문서 임베딩 생성 및 검색 서비스
    
    OpenAI API를 사용하여 텍스트 임베딩을 생성하고
    PostgreSQL pgvector에 저장 및 검색하는 기능 제공
    """
    
    def __init__(self):
        """OpenAI 클라이언트 초기화"""
        self.openai_client = OpenAI(api_key=settings.AI_API_KEY)
        self.async_openai_client = AsyncOpenAI(api_key=settings.AI_API_KEY)
        self.embedding_model = settings.AI_EMBEDDING_MODEL or "text-embedding-ada-002"
        self.embedding_dimension = 1536  # OpenAI 모델 기본 차원
        
    def create_embedding(self, text: str) -> List[float]:
        """
        텍스트에 대한 임베딩 생성 (동기 방식)
        
        Args:
            text: 임베딩할 텍스트
            
        Returns:
            임베딩 벡터 (float 리스트)
        """
        try:
            # 빈 텍스트 처리
            if not text or len(text.strip()) == 0:
                return [0.0] * self.embedding_dimension
                
            # OpenAI API로 임베딩 생성
            response = self.openai_client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            
            # 임베딩 결과 반환
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {str(e)}")
            # 오류 발생 시 0 벡터 반환
            return [0.0] * self.embedding_dimension
    
    async def create_embedding_async(self, text: str) -> List[float]:
        """
        텍스트에 대한 임베딩 생성 (비동기 방식)
        
        Args:
            text: 임베딩할 텍스트
            
        Returns:
            임베딩 벡터 (float 리스트)
        """
        try:
            # 빈 텍스트 처리
            if not text or len(text.strip()) == 0:
                return [0.0] * self.embedding_dimension
                
            # OpenAI API로 임베딩 생성 (비동기)
            response = await self.async_openai_client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            
            # 임베딩 결과 반환
            return response.data[0].embedding
            
        except Exception as e:
            logger.error(f"비동기 임베딩 생성 실패: {str(e)}")
            # 오류 발생 시 0 벡터 반환
            return [0.0] * self.embedding_dimension
    
    async def create_embeddings_batch(self, texts: List[str], batch_size: int = 10) -> List[List[float]]:
        """
        여러 텍스트에 대한 임베딩을 배치 단위로 생성 (비동기)
        
        Args:
            texts: 임베딩할 텍스트 리스트
            batch_size: API 호출당 최대 텍스트 수
            
        Returns:
            임베딩 벡터 리스트
        """
        results = []
        
        # 텍스트를 배치로 분할
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i+batch_size]
            
            try:
                # OpenAI API로 배치 임베딩 생성 (비동기)
                response = await self.async_openai_client.embeddings.create(
                    input=batch,
                    model=self.embedding_model
                )
                
                # 벡터 추출 및 결과에 추가
                batch_embeddings = [item.embedding for item in response.data]
                results.extend(batch_embeddings)
                
                # API 요청 제한 방지를 위한 짧은 대기
                if i + batch_size < len(texts):
                    await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"배치 임베딩 생성 실패 (인덱스 {i}-{i+batch_size}): {str(e)}")
                # 오류 발생 시 0 벡터로 채움
                for _ in range(len(batch)):
                    results.append([0.0] * self.embedding_dimension)
        
        return results
    
    def store_chunk_embedding(
        self, 
        db: Session, 
        document_id: int, 
        chunk_index: int, 
        text: str, 
        start_char: int, 
        end_char: int, 
        embedding: List[float]
    ) -> bool:
        """
        문서 청크 임베딩을 데이터베이스에 저장
        
        Args:
            db: 데이터베이스 세션
            document_id: PDF 문서 ID
            chunk_index: 청크 인덱스
            text: 청크 텍스트
            start_char: 시작 문자 위치
            end_char: 종료 문자 위치
            embedding: 임베딩 벡터
            
        Returns:
            성공 여부
        """
        try:
            # pgvector INSERT 쿼리 생성
            query = text("""
                INSERT INTO document_chunks 
                (document_id, chunk_index, text, start_char, end_char, embedding, created_at) 
                VALUES (:document_id, :chunk_index, :text, :start_char, :end_char, :embedding::vector, NOW())
                ON CONFLICT (document_id, chunk_index) 
                DO UPDATE SET 
                    text = EXCLUDED.text,
                    start_char = EXCLUDED.start_char,
                    end_char = EXCLUDED.end_char,
                    embedding = EXCLUDED.embedding,
                    created_at = NOW()
            """)
            
            # 쿼리 실행
            db.execute(query, {
                "document_id": document_id,
                "chunk_index": chunk_index,
                "text": text,
                "start_char": start_char,
                "end_char": end_char,
                "embedding": json.dumps(embedding) # PostgreSQL이 vector 타입으로 변환
            })
            
            db.commit()
            return True
            
        except Exception as e:
            logger.error(f"청크 임베딩 저장 실패: {str(e)}")
            db.rollback()
            return False
            
    async def store_chunk_embeddings_batch(
        self, 
        db: Session, 
        document_id: int, 
        chunks: List[Dict[str, Any]]
    ) -> Tuple[int, int]:
        """
        여러 문서 청크 임베딩을 배치로 저장
        
        Args:
            db: 데이터베이스 세션
            document_id: PDF 문서 ID
            chunks: 청크 정보 딕셔너리 리스트 (text, index, start_char, end_char 포함)
            
        Returns:
            (성공 수, 실패 수) 튜플
        """
        success_count = 0
        failure_count = 0
        
        # 모든 청크의 텍스트 추출
        chunk_texts = [chunk["text"] for chunk in chunks]
        
        # 일괄 임베딩 생성
        embeddings = await self.create_embeddings_batch(chunk_texts)
        
        # 각 청크 및 임베딩 저장
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            success = self.store_chunk_embedding(
                db=db,
                document_id=document_id,
                chunk_index=chunk["index"],
                text=chunk["text"],
                start_char=chunk.get("start_char", 0),
                end_char=chunk.get("end_char", len(chunk["text"])),
                embedding=embedding
            )
            
            if success:
                success_count += 1
            else:
                failure_count += 1
                
            # 주기적으로 진행 상황 로깅
            if (i + 1) % 10 == 0:
                logger.info(f"임베딩 저장 진행 중: {i+1}/{len(chunks)} 처리됨")
        
        return success_count, failure_count
        
    def search_similar_chunks(
        self, 
        db: Session, 
        document_id: int, 
        query_text: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        쿼리와 유사한 문서 청크 검색
        
        Args:
            db: 데이터베이스 세션
            document_id: PDF 문서 ID
            query_text: 검색 쿼리 텍스트
            limit: 반환할 최대 결과 수
            
        Returns:
            유사한 청크 목록 (유사도 점수 포함)
        """
        try:
            # 쿼리 텍스트 임베딩 생성
            query_embedding = self.create_embedding(query_text)
            
            # 유사도 검색 쿼리 실행
            query = text("""
                SELECT 
                    id, 
                    document_id, 
                    chunk_index, 
                    text, 
                    start_char, 
                    end_char,
                    1 - (embedding <=> :query_embedding::vector) AS similarity
                FROM document_chunks
                WHERE document_id = :document_id
                ORDER BY embedding <=> :query_embedding::vector
                LIMIT :limit
            """)
            
            result = db.execute(query, {
                "document_id": document_id,
                "query_embedding": json.dumps(query_embedding),
                "limit": limit
            }).fetchall()
            
            # 결과 형식화
            chunks = []
            for row in result:
                chunks.append({
                    "id": row.id,
                    "document_id": row.document_id,
                    "index": row.chunk_index,
                    "text": row.text,
                    "start_char": row.start_char,
                    "end_char": row.end_char,
                    "similarity": float(row.similarity)
                })
            
            return chunks
            
        except Exception as e:
            logger.error(f"유사 청크 검색 실패: {str(e)}")
            return []

    async def search_similar_chunks_async(
        self, 
        db: Session, 
        document_id: int, 
        query_text: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        쿼리와 유사한 문서 청크 검색 (비동기)
        
        Args:
            db: 데이터베이스 세션
            document_id: PDF 문서 ID
            query_text: 검색 쿼리 텍스트
            limit: 반환할 최대 결과 수
            
        Returns:
            유사한 청크 목록 (유사도 점수 포함)
        """
        try:
            # 쿼리 텍스트 임베딩 생성 (비동기)
            query_embedding = await self.create_embedding_async(query_text)
            
            # 비동기 함수에서 동기 DB 작업 실행
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                None,
                self._execute_similarity_search,
                db, document_id, query_embedding, limit
            )
            
        except Exception as e:
            logger.error(f"비동기 유사 청크 검색 실패: {str(e)}")
            return []
            
    def _execute_similarity_search(
        self, 
        db: Session, 
        document_id: int, 
        query_embedding: List[float], 
        limit: int
    ) -> List[Dict[str, Any]]:
        """
        임베딩 기반 유사도 검색 실행 (내부 동기 메서드)
        """
        try:
            # 유사도 검색 쿼리 실행
            query = text("""
                SELECT 
                    id, 
                    document_id, 
                    chunk_index, 
                    text, 
                    start_char, 
                    end_char,
                    1 - (embedding <=> :query_embedding::vector) AS similarity
                FROM document_chunks
                WHERE document_id = :document_id
                ORDER BY embedding <=> :query_embedding::vector
                LIMIT :limit
            """)
            
            result = db.execute(query, {
                "document_id": document_id,
                "query_embedding": json.dumps(query_embedding),
                "limit": limit
            }).fetchall()
            
            # 결과 형식화
            chunks = []
            for row in result:
                chunks.append({
                    "id": row.id,
                    "document_id": row.document_id,
                    "index": row.chunk_index,
                    "text": row.text,
                    "start_char": row.start_char,
                    "end_char": row.end_char,
                    "similarity": float(row.similarity)
                })
            
            return chunks
            
        except Exception as e:
            logger.error(f"유사도 검색 실행 실패: {str(e)}")
            return []