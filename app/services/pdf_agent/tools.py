# app/services/pdf_agent/tools.py

from typing import Dict, Any, List, Optional
from langchain_core.messages import SystemMessage
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
import os
import logging
from dotenv import load_dotenv
from app.core.config import settings

# 로깅 설정
logger = logging.getLogger(__name__)

# 환경 변수 로드
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY", "")

def get_initial_state(
    user_id: str,
    document_id: int,
    pdf_path: str,
    purpose: str,
    folder: str = "default",
    query: Optional[str] = ""
) -> Dict[str, Any]:
    """
    LangGraph 초기 상태 생성
    
    Returns:
        초기화된 상태 딕셔너리
    """
    return {
        "messages": [
            SystemMessage(content="""당신은 학생들을 가르치는 것으로 국내 0.1%의 명성을 가진 교육자입니다.
            다음 사용자의 요청에 따라 작업을 수행해주시면 됩니다. 사용자의 요청은 총 4가지로 이루어져 있습니다.
            1. 질의 응답, 2. 학습 자료 요약, 3. 시험 문제 생성, 4. 학습 계획 세우기입니다.
            특히 질의 응답의 경우, 자료에 근거하여 답변해주시되, 질문에 답하기 위한 좋은 자료가 존재하지 않다면, 당신이 아는 지식으로 답변해주시면 됩니다.
            사용자의 요청에 친절하고 자세한 설명으로 국내 0.1% 명성에 맞게 학습자의 이해를 도와주시면 됩니다.""")
        ],
        "last_user_query": "",
        "last_assistant_response": "",
        "user_id": user_id,
        "document_id": document_id,
        "pdf_path": pdf_path,
        "purpose": purpose,
        "folder": folder,
        "pdf_text": "",
        "structure": {},
        "doc_chunks": [],
        "summaries": "",
        "result": "",
        "explain_step": 0,
        "need_to_explain": {},
        "subject_index": 0,
        "final_index": [],
        "personality": [],
        "final_personality": "",
        "embedding_stored": False,
        "error": None
    }


def search_documents_for_qa(user_id: str, folder: str, query: str, k: int = 2) -> List[Dict[str, Any]]:
    """
    질의응답을 위한 문서 검색
    
    Args:
        user_id: 사용자 ID
        folder: 폴더명
        query: 검색 쿼리
        k: 반환할 결과 수
        
    Returns:
        관련 문서 목록
    """
    try:
        # 사용자 ChromaDB 경로
        user_dir = f"{settings.CHROMADB_STORAGE_PATH}"  # 루트 ChromaDB 경로 사용
        
        # 경로 존재 확인
        if not os.path.exists(user_dir):
            logger.warning(f"사용자 ChromaDB 경로가 존재하지 않음: {user_dir}")
            return []
        
        # 임베딩 모델 초기화
        embeddings = OpenAIEmbeddings(api_key=API_KEY)
        
        # ChromaDB 로드
        vectorstore = Chroma(persist_directory=user_dir, embedding_function=embeddings)
        
        filter_condition = {"folder": folder}
        if user_id:
            # user_id가 정수 문자열인 경우 정수로 변환
            try:
                user_id_int = int(user_id)
                collection_name = f"user_{user_id_int}_{folder}"
            except ValueError:
                collection_name = f"user_{user_id}_{folder}"

        # 유사도 검색 실행
        results = vectorstore.similarity_search_with_score(
            query, 
            k=k,
            filter_condition=filter_condition,
            collection_name=collection_name
        )
        
        # 결과 필터링 및 반환
        return [doc for doc, score in results if score < 0.8]  # 점수가 낮을수록 유사도 높음
        
    except Exception as e:
        logger.error(f"문서 검색 실패: {str(e)}")
        return []


def search_documents_for_summary(user_id: str, folder: str, query: str = None, k: int = 1) -> List[Dict[str, Any]]:
    """
    요약을 위한 문서 검색
    
    Args:
        user_id: 사용자 ID
        folder: 폴더명
        query: 검색 쿼리 (선택 사항)
        k: 반환할 결과 수
        
    Returns:
        관련 문서 목록
    """
    try:
        # ChromaDB 서비스 사용
        from app.services.pdf_agent.chromadb_service import ChromaDBService
        
        logger.info(f"문서 검색 시작: user_id={user_id}, folder={folder}, query={'있음' if query else '없음'}")
        
        # 정수형 user_id로 변환 (문자열 입력 처리)
        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            user_id_int = None
            logger.warning(f"user_id를 정수로 변환할 수 없음: {user_id}")
        
        # ChromaDB 서비스 인스턴스 가져오기
        chroma_service = ChromaDBService()
        
        # 관련 문서 검색 - 구체적인 예외 처리
        try:
            # 사용자 컬렉션 이름 생성
            collection_name = f"user_{user_id}_{folder}"
            
            # 컬렉션 확인 및 검색 실행
            if query:
                logger.info(f"쿼리 기반 검색 시작: query='{query}', collection={collection_name}")
                
                # 해당 사용자가 소유한 문서 검색 (전체 문서 대상)
                docs = chroma_service.search_across_documents(
                    user_id=user_id_int,
                    query_text=query,
                    folder_name=folder,
                    limit=k
                )
                
                if docs:
                    logger.info(f"검색 결과: {len(docs)}개 문서 발견")
                    return docs
                else:
                    # DB에서 직접 문서 검색 시도
                    logger.warning(f"ChromaDB에서 문서를 찾을 수 없음, DB에서 직접 검색 시도")
                    from app.db.session import SessionLocal
                    from app.models.tag import PDFFile
                    
                    db = SessionLocal()
                    try:
                        pdf_files = db.query(PDFFile).filter(PDFFile.owner_id == user_id_int).all()
                        if pdf_files:
                            logger.info(f"DB에서 {len(pdf_files)}개 문서 발견")
                            
                            # 첫 번째 문서 사용 (더 나은 방법으로 개선 가능)
                            pdf_file = pdf_files[0]
                            return [{
                                "document_id": pdf_file.id,
                                "text": f"파일명: {pdf_file.filename}\n경로: {pdf_file.file_path}",
                                "metadata": {"document_id": pdf_file.id}
                            }]
                    finally:
                        db.close()
            else:
                # 쿼리 없이 모든 문서 가져오기
                logger.info(f"모든 문서 검색 시작: collection={collection_name}")
                from app.db.session import SessionLocal
                from app.models.tag import PDFFile
                
                db = SessionLocal()
                try:
                    pdf_files = db.query(PDFFile).filter(PDFFile.owner_id == user_id_int).all()
                    if pdf_files:
                        logger.info(f"DB에서 {len(pdf_files)}개 문서 발견")
                        
                        # 첫 번째 문서 사용
                        pdf_file = pdf_files[0]
                        return [{
                            "document_id": pdf_file.id,
                            "text": f"파일명: {pdf_file.filename}\n경로: {pdf_file.file_path}",
                            "metadata": {"document_id": pdf_file.id}
                        }]
                finally:
                    db.close()
                
            # 여기까지 왔다면 문서를 찾지 못한 것
            raise ValueError(f"관련 PDF 문서를 찾을 수 없습니다. user_id={user_id}, folder={folder}, query='{query}'")
            
        except Exception as search_err:
            logger.error(f"문서 검색 중 오류: {str(search_err)}", exc_info=True)
            raise  # 상위로 예외 전파
            
    except Exception as e:
        logger.error(f"요약용 문서 검색 실패: {str(e)}", exc_info=True)
        
        # 마지막 수단: DB에서 직접 문서 검색
        try:
            from app.db.session import SessionLocal
            from app.models.tag import PDFFile
            
            db = SessionLocal()
            try:
                user_id_int = int(user_id) if isinstance(user_id, str) else user_id
                pdf_files = db.query(PDFFile).filter(PDFFile.owner_id == user_id_int).all()
                if pdf_files:
                    logger.info(f"최종 대체 검색: DB에서 {len(pdf_files)}개 문서 발견")
                    
                    # 첫 번째 문서 반환
                    pdf_file = pdf_files[0]
                    return [{
                        "document_id": pdf_file.id,
                        "text": f"파일명: {pdf_file.filename}\n경로: {pdf_file.file_path}",
                        "metadata": {"document_id": pdf_file.id}
                    }]
            finally:
                db.close()
        except Exception as db_err:
            logger.error(f"DB 대체 검색 실패: {str(db_err)}")
        
        return []


def search_documents_for_exam(user_id: str, folder: str) -> List[Dict[str, Any]]:
    """
    시험 문제 생성을 위한 문서 검색
    
    Args:
        user_id: 사용자 ID
        folder: 폴더명
        
    Returns:
        문서 목록
    """
    try:
        # 사용자 ChromaDB 경로
        user_dir = f"{user_id}/chroma/{folder}"
        
        # 경로 존재 확인
        if not os.path.exists(user_dir):
            logger.warning(f"사용자 ChromaDB 경로가 존재하지 않음: {user_dir}")
            return []
        
        # 임베딩 모델 초기화
        embeddings = OpenAIEmbeddings(api_key=API_KEY)
        
        # ChromaDB 로드
        vectorstore = Chroma(persist_directory=user_dir, embedding_function=embeddings)
        
        # 전체 문서 가져오기
        documents = vectorstore.get(filter={"is_full_document": True})
        
        return documents
        
    except Exception as e:
        logger.error(f"시험용 문서 검색 실패: {str(e)}")
        return []


def search_documents_for_scheduler(user_id: str, folder: str) -> List[Dict[str, Any]]:
    """
    학습 계획 생성을 위한 문서 검색
    
    Args:
        user_id: 사용자 ID
        folder: 폴더명
        
    Returns:
        문서 목록
    """
    try:
        # 사용자 ChromaDB 경로
        user_dir = f"{user_id}/chroma/{folder}"
        
        # 경로 존재 확인
        if not os.path.exists(user_dir):
            logger.warning(f"사용자 ChromaDB 경로가 존재하지 않음: {user_dir}")
            return []
        
        # 임베딩 모델 초기화
        embeddings = OpenAIEmbeddings(api_key=API_KEY)
        
        # ChromaDB 로드
        vectorstore = Chroma(persist_directory=user_dir, embedding_function=embeddings)
        
        # 인덱스 정보가 있는 문서 검색
        documents = vectorstore.get(filter={"indices": True})
        
        return documents
        
    except Exception as e:
        logger.error(f"스케줄러용 문서 검색 실패: {str(e)}")
        return []