import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from app.core.config import settings

logger = logging.getLogger(__name__)

class ChromaDBService:
    """
    ChromaDB를 사용한 문서 임베딩 및 검색 서비스
    각 사용자마다 별도의 컬렉션을 관리합니다.
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChromaDBService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """ChromaDB 클라이언트 초기화"""
        try:
            self.db_path = os.path.join("/app/storage/chromadb")
            os.makedirs(self.db_path, exist_ok=True)

            self.client = chromadb.PersistentClient(
                path=self.db_path,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )

            self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                api_key=settings.AI_API_KEY,
                model_name="text-embedding-ada-002"
            )

            logger.info(f"ChromaDB 초기화 성공: {self.db_path}")

        except Exception as e:
            logger.error(f"ChromaDB 초기화 실패: {str(e)}")
            self.client = None

    def _get_user_collection(self, user_id: int, create_if_not_exists: bool = True):
        """사용자별 컬렉션 가져오기 (없으면 생성)"""
        if not self.client:
            logger.error("ChromaDB 클라이언트가 초기화되지 않았습니다.")
            return None

        collection_name = f"user_{user_id}_vstore"

        try:
            collections = self.client.list_collections()
            collection_exists = any(c.name == collection_name for c in collections)

            if collection_exists:
                return self.client.get_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function
                )
            elif create_if_not_exists:
                return self.client.create_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function,
                    metadata={"user_id": user_id}
                )
            else:
                return None

        except Exception as e:
            logger.error(f"사용자 컬렉션 접근 실패: {str(e)}")
            return None

    def add_document_chunks(self, user_id: int, document_id: int, chunks: List[Dict[str, Any]]) -> bool:
        collection = self._get_user_collection(user_id)
        if not collection:
            return False

        try:
            self.delete_document_chunks(user_id, document_id)

            ids = []
            texts = []
            metadatas = []

            for chunk in chunks:
                chunk_id = f"doc_{document_id}_chunk_{chunk['index']}"
                ids.append(chunk_id)
                texts.append(chunk["text"])
                metadatas.append({
                    "document_id": document_id,
                    "chunk_index": chunk["index"],
                    "start_char": chunk.get("start_char", 0),
                    "end_char": chunk.get("end_char", len(chunk["text"])),
                    "page": chunk.get("page", 1)
                })

            collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )

            logger.info(f"문서 {document_id}의 {len(chunks)}개 청크를 ChromaDB에 저장했습니다.")
            return True

        except Exception as e:
            logger.error(f"ChromaDB 청크 추가 실패: {str(e)}")
            return False

    def delete_document_chunks(self, user_id: int, document_id: int) -> bool:
        collection = self._get_user_collection(user_id, create_if_not_exists=False)
        if not collection:
            return False

        try:
            collection.delete(
                where={"document_id": document_id}
            )

            logger.info(f"문서 {document_id}의 모든 청크가 삭제되었습니다.")
            return True

        except Exception as e:
            logger.error(f"ChromaDB 청크 삭제 실패: {str(e)}")
            return False

    def search_similar_chunks(
        self,
        user_id: int,
        document_id: int,
        query_text: str,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        collection = self._get_user_collection(user_id, create_if_not_exists=False)
        if not collection:
            return []

        try:
            results = collection.query(
                query_texts=[query_text],
                where={"document_id": document_id},
                n_results=limit
            )

            chunks = []
            if not results["documents"]:
                return []

            for i, (doc, metadata, distance) in enumerate(zip(
                results["documents"][0],
                results["metadatas"][0],
                results["distances"][0] if "distances" in results else [0] * len(results["documents"][0])
            )):
                similarity = 1.0 - float(distance) if distance else 0.95
                chunks.append({
                    "document_id": document_id,
                    "index": metadata["chunk_index"],
                    "text": doc,
                    "start_char": metadata.get("start_char", 0),
                    "end_char": metadata.get("end_char", len(doc)),
                    "page": metadata.get("page", 1),
                    "similarity": similarity
                })

            chunks.sort(key=lambda x: x["similarity"], reverse=True)
            return chunks

        except Exception as e:
            logger.error(f"ChromaDB 검색 실패: {str(e)}")
            return []