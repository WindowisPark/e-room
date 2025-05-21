import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions
from app.core.config import settings

logger = logging.getLogger(__name__)

# 파일 상단에 더미 클라이언트 클래스 추가
class DummyChromaClient:
    """ChromaDB 클라이언트가 초기화되지 않을 때 사용하는 더미 클라이언트"""
    
    def __getattr__(self, name):
        def dummy_method(*args, **kwargs):
            logger.warning(f"ChromaDB 클라이언트가 초기화되지 않았습니다. {name} 메서드 호출이 무시됩니다.")
            return None
        return dummy_method
    
class ChromaDBService:
    """
    ChromaDB를 사용한 문서 임베딩 및 검색 서비스
    각 사용자마다 별도의 컬렉션을 관리합니다.
    """

    _instance = None
    _initialized = False  # 초기화 여부 추적

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ChromaDBService, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        # 이미 초기화되었으면 생략
        if not ChromaDBService._initialized:
            self._initialize()
            ChromaDBService._initialized = True

    def _initialize(self):
        """ChromaDB 클라이언트 초기화"""
        try:
            self.db_path = settings.CHROMADB_STORAGE_PATH
            os.makedirs(self.db_path, exist_ok=True)

            # 클라이언트 설정 일관성 유지
            client_settings = Settings(
                anonymized_telemetry=False,
                allow_reset=True,  # 필요시 재설정 허용
                persist_directory=self.db_path
            )
            
            try:
                # ChromaDB 클라이언트 초기화 시도
                self.client = chromadb.PersistentClient(
                    path=self.db_path,
                    settings=client_settings
                )
                
                # API 키 확인
                api_key = os.getenv("OPENAI_API_KEY", "") or settings.AI_API_KEY
                logger.info(f"API 키 설정 상태: {'설정됨' if api_key else '설정 안 됨'}")
                
                if api_key:
                    # OpenAI 임베딩 함수 설정
                    try:
                        # API 키 마스킹하여 로깅 (보안)
                        masked_key = api_key[:4] + "..." + api_key[-4:] if len(api_key) > 8 else "***"
                        logger.info(f"OpenAI API 키: {masked_key}")
                        
                        self.embedding_function = embedding_functions.OpenAIEmbeddingFunction(
                            api_key=api_key,
                            model_name="text-embedding-ada-002"
                        )
                        logger.info("OpenAI 임베딩 함수 초기화 성공")
                    except Exception as emb_err:
                        logger.error(f"OpenAI 임베딩 함수 초기화 실패: {str(emb_err)}")
                        self.embedding_function = None
                else:
                    logger.warning("AI_API_KEY가 설정되지 않았습니다. 임베딩 기능이 제한됩니다.")
                    self.embedding_function = None
                
                logger.info(f"ChromaDB 초기화 성공: {self.db_path}")
                
            except Exception as client_err:
                logger.error(f"ChromaDB 클라이언트 초기화 실패: {str(client_err)}")
                self.client = DummyChromaClient()  # 더미 클라이언트 사용
                self.embedding_function = None
                
        except Exception as e:
            logger.error(f"ChromaDB 서비스 초기화 실패: {str(e)}")
            self.client = DummyChromaClient()  # 더미 클라이언트 사용
            self.embedding_function = None

    def _get_user_collection(self, user_id: int, folder_name: str = "default", create_if_not_exists: bool = True):
        """사용자별 컬렉션 가져오기 (없으면 생성)"""
        if not self.client:
            logger.error("ChromaDB 클라이언트가 초기화되지 않았습니다.")
            return None
        
        # 사용자_폴더_저장소 형태의 컬렉션 이름 사용
        collection_name = f"user_{user_id}_{folder_name}"

        try:
            collections = self.client.list_collections()
            collection_exists = any(c.name == collection_name for c in collections)

            if collection_exists:
                if self.embedding_function:
                    return self.client.get_collection(
                        name=collection_name,
                        embedding_function=self.embedding_function
                    )
                else:
                    # 임베딩 함수 없이 컬렉션 가져오기
                    return self.client.get_collection(name=collection_name)
            elif create_if_not_exists:
                if self.embedding_function:
                    return self.client.create_collection(
                        name=collection_name,
                        embedding_function=self.embedding_function,
                        metadata={"user_id": user_id, "folder": folder_name}
                    )
                else:
                    # 임베딩 함수 없이 컬렉션 생성
                    return self.client.create_collection(
                        name=collection_name,
                        metadata={"user_id": user_id, "folder": folder_name}
                    )
            else:
                return None

        except Exception as e:
            logger.error(f"사용자 컬렉션 접근 실패: {str(e)}")
            return None
        
    def add_document_chunks(self, user_id: int, document_id: int, folder_name: str, chunks: List[Dict[str, Any]]) -> bool:
        collection = self._get_user_collection(user_id, folder_name=folder_name)
        if not collection:
            logger.error(f"컬렉션을 가져오지 못함: user_id={user_id}, folder={folder_name}")
            return False

        try:
            # 기존 청크 삭제
            logger.info(f"기존 문서 청크 삭제 시작: doc_id={document_id}")
            self.delete_document_chunks(user_id, document_id, folder_name)

            ids = []
            texts = []
            metadatas = []

            logger.info(f"청크 데이터 준비 시작: 총 {len(chunks)}개 청크")
            for chunk in chunks:
                chunk_id = f"doc_{document_id}_chunk_{chunk['index']}"
                ids.append(chunk_id)
                texts.append(chunk["text"])
                metadatas.append({
                    "document_id": document_id,
                    "folder": folder_name,
                    "chunk_index": chunk["index"],
                    "start_char": chunk.get("start_char", 0),
                    "end_char": chunk.get("end_char", len(chunk["text"])),
                    "page": chunk.get("page", 1)
                })

            logger.info(f"ChromaDB에 청크 추가 시작: {len(ids)}개 항목")
            logger.debug(f"첫 번째 청크 ID: {ids[0] if ids else 'N/A'}")
            logger.debug(f"첫 번째 청크 텍스트: {texts[0][:100] if texts else 'N/A'}...")

            # 임베딩 함수 로깅
            emb_func_info = "사용 중" if self.embedding_function else "사용 안 함"
            logger.info(f"임베딩 함수: {emb_func_info}")

            collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas
            )

            logger.info(f"문서 {document_id}의 {len(chunks)}개 청크를 ChromaDB에 성공적으로 저장했습니다.")
            return True

        except Exception as e:
            logger.error(f"ChromaDB 청크 추가 실패: {str(e)}", exc_info=True)
            return False

    def delete_document_chunks(self, user_id: int, document_id: int, folder_name: str = "default") -> bool:
        collection = self._get_user_collection(user_id, folder_name=folder_name, create_if_not_exists=False)
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
        folder_name: str = "default",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        collection = self._get_user_collection(
            user_id, 
            folder_name=folder_name, 
            create_if_not_exists=False
        )
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
        
    def check_document_exists(self, user_id: int, document_id: int, folder_name: str = "default") -> bool:
        """문서가 이미 ChromaDB에 저장되어 있는지 확인"""
        collection = self._get_user_collection(user_id, folder_name=folder_name, create_if_not_exists=False)
        if not collection:
            return False

        try:
            # 임베딩 요청을 피하기 위해 get 메서드 사용
            # where 조건으로 document_id 필터링
            results = collection.get(
                where={"document_id": document_id},
                limit=1
            )
            
            # 결과가 있으면 문서가 존재
            if results and results.get("ids") and len(results["ids"]) > 0:
                return True
            return False
            
        except Exception as e:
            logger.error(f"문서 존재 확인 실패: {str(e)}")
            return False

    def count_document_chunks(self, user_id: int, document_id: int, folder_name: str = "default") -> int:
        """문서의 청크 개수 조회"""
        collection = self._get_user_collection(user_id, folder_name=folder_name, create_if_not_exists=False)
        if not collection:
            return 0

        try:
            # get 메서드 사용
            results = collection.get(
                where={"document_id": document_id}
            )
            
            # 반환된 문서 수
            if results and results.get("ids"):
                return len(results["ids"])
            return 0
            
        except Exception as e:
            logger.error(f"문서 청크 수 조회 실패: {str(e)}")
            return 0
        
    def search_across_documents(
        self,
        user_id: int,
        query_text: str,
        folder_name: str = "default",
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """모든 문서에 걸쳐 가장 관련성 높은 청크 검색"""
        collection_name = f"user_{user_id}_{folder_name}"
        
        try:
            # 컬렉션 가져오기(없으면 생성하지 않음)
            collection = self._get_user_collection(user_id, folder_name=folder_name, create_if_not_exists=False)
            
            if not collection:
                logger.warning(f"컬렉션을 찾을 수 없음: {collection_name}")
                # DB에서 문서 검색 시도
                try:
                    from app.db.session import SessionLocal
                    from app.models.tag import PDFFile
                    
                    db = SessionLocal()
                    try:
                        pdf_file = db.query(PDFFile).filter(PDFFile.owner_id == user_id).first()
                        if pdf_file:
                            logger.info(f"대체 문서 사용: id={pdf_file.id}, name={pdf_file.filename}")
                            return [{
                                "document_id": pdf_file.id,
                                "text": f"파일명: {pdf_file.filename}\n경로: {pdf_file.file_path}",
                                "similarity": 0.5
                            }]
                    finally:
                        db.close()
                except Exception as db_err:
                    logger.error(f"대체 문서 검색 오류: {str(db_err)}")
                
                return []

            # 임베딩 함수 확인
            embedding_function = self.embedding_function
            
            # 임베딩 함수가 없으면 메타데이터 기반 검색
            if not embedding_function:
                logger.warning("임베딩 함수가 없음, 메타데이터 기반 검색")
                # collection.get() 대신 db에서 직접 검색
                try:
                    from app.db.session import SessionLocal
                    from app.models.tag import PDFFile
                    
                    db = SessionLocal()
                    try:
                        pdf_files = db.query(PDFFile).filter(PDFFile.owner_id == user_id).limit(limit).all()
                        
                        chunks = []
                        for pdf in pdf_files:
                            chunks.append({
                                "document_id": pdf.id,
                                "text": f"파일명: {pdf.filename}",
                                "similarity": 0.5  # 임의의 유사도
                            })
                        
                        return chunks
                    finally:
                        db.close()
                except Exception as db_err:
                    logger.error(f"DB 검색 오류: {str(db_err)}")
                    return []
            
            # 정상 임베딩 검색 시도
            try:
                results = collection.query(
                    query_texts=[query_text],
                    n_results=limit
                )
                
                chunks = []
                if not results.get("documents") or not results["documents"][0]:
                    return []
                    
                for i, (doc, metadata, distance) in enumerate(zip(
                    results["documents"][0],
                    results["metadatas"][0],
                    results["distances"][0] if "distances" in results else [0] * len(results["documents"][0])
                )):
                    similarity = 1.0 - float(distance) if distance else 0.95
                    chunks.append({
                        "document_id": metadata.get("document_id", 0),
                        "index": metadata.get("chunk_index", 0),
                        "text": doc,
                        "similarity": similarity
                    })
                    
                # 유사도 기준으로 정렬
                chunks.sort(key=lambda x: x["similarity"], reverse=True)
                return chunks
                
            except Exception as search_err:
                logger.error(f"ChromaDB 검색 실패: {str(search_err)}")
                # DB 검색으로 대체
                try:
                    from app.db.session import SessionLocal
                    from app.models.tag import PDFFile
                    
                    db = SessionLocal()
                    try:
                        pdf_files = db.query(PDFFile).filter(PDFFile.owner_id == user_id).limit(limit).all()
                        
                        chunks = []
                        for pdf in pdf_files:
                            chunks.append({
                                "document_id": pdf.id,
                                "text": f"파일명: {pdf.filename}",
                                "similarity": 0.5  # 임의의 유사도
                            })
                        
                        return chunks
                    finally:
                        db.close()
                except Exception as db_err:
                    logger.error(f"DB 검색 오류: {str(db_err)}")
                    return []
                
        except Exception as e:
            logger.error(f"전체 문서 검색 실패: {str(e)}")
            return []