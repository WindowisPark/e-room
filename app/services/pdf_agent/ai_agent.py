# app/services/pdf_agent/ai_agent.py (update)

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
import os
import tempfile
from sqlalchemy.orm import Session

from app.models.tag import PDFFile
from app.services.pdf_agent.processor import PDFProcessor
from app.services.pdf_agent.embedding_service import EmbeddingService
from app.core.config import settings

# AI 서비스 통합
from app.services.pdf_agent.ai_service import PDFAIService

logger = logging.getLogger(__name__)

# 싱글톤 패턴으로 AI 서비스 초기화
pdf_ai_service = PDFAIService()

class PDFAgent:
    """
    PDF 관련 AI 기능 제공 클래스
    - 문서 요약, 질문 생성, 질의응답 등 기능 제공
    """
    
    @staticmethod
    async def generate_answer(query: str, contexts: List[str]) -> str:
        """
        질문에 대한 답변 생성
        
        Args:
            query: 질문 내용
            contexts: 관련 문맥 정보 (문서 청크)
            
        Returns:
            생성된 답변
        """
        try:
            # 기존 OpenAI API 기반 코드 유지
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=settings.AI_API_KEY)
            
            # 컨텍스트 결합
            combined_context = "\n\n".join([f"청크 {i+1}: {ctx}" for i, ctx in enumerate(contexts)])
            
            # 프롬프트 구성
            prompt = f"""
            다음 문서 청크를 기반으로 질문에 답변해주세요.
            
            문서 내용:
            {combined_context}
            
            질문: {query}
            
            답변은 문서 내용을 기반으로 작성해야 합니다. 정확한 정보를 제공하고, 문서에 없는 내용은 지어내지 마세요.
            문서에 답이 없다면 "이 질문에 대한 답변을 문서에서 찾을 수 없습니다."라고 알려주세요.
            """
            
            # 모델 호출
            response = await client.chat.completions.create(
                model=settings.AI_MODEL_NAME,
                messages=[
                    {"role": "system", "content": "당신은 문서 기반 질의응답을 제공하는 AI 어시스턴트입니다. 주어진 문서 내용만을 기반으로 정확하고 관련성 높은 답변을 제공하세요."}, 
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            
            # 답변 추출
            answer = response.choices[0].message.content.strip()
            return answer
            
        except Exception as e:
            logger.error(f"답변 생성 실패: {str(e)}", exc_info=True)
            return "답변 생성 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요."
    
    @staticmethod
    async def summarize(db: Session, document_id: int, level: str = "default") -> Dict[str, Any]:
        """
        문서 요약 생성 - LangGraph 기반 처리
        
        Args:
            db: 데이터베이스 세션
            document_id: 문서 ID
            level: 요약 수준 (default, short, detailed)
            
        Returns:
            요약 결과 (성공 여부, 요약 텍스트 등)
        """
        try:
            # 임베딩 서비스 초기화
            embedding_service = EmbeddingService()
            
            # 문서 조회
            pdf_file = db.query(PDFFile).filter(PDFFile.id == document_id).first()
            if not pdf_file:
                return {"success": False, "error": "문서를 찾을 수 없습니다"}
            
            # 파일 경로 확인
            file_path = pdf_file.file_path
            if not os.path.exists(file_path):
                return {"success": False, "error": "파일을 찾을 수 없습니다"}
            
            # LangGraph 워크플로우 실행
            logger.info(f"문서 요약 시작: {document_id}, 파일: {file_path}")
            result = pdf_ai_service.process_pdf(file_path)
            
            if not result.get("success", False):
                error_msg = result.get("error", "알 수 없는 오류")
                logger.error(f"문서 요약 실패: {error_msg}")
                return result
            
            # 요약 결과 반환
            logger.info(f"문서 요약 완료: {document_id}")
            return {
                "success": True,
                "document_id": document_id,
                "document_name": pdf_file.filename,
                "summary": result["result"],
                "summary_level": level,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"요약 생성 실패: {str(e)}", exc_info=True)
            return {"success": False, "error": f"요약 생성 중 오류 발생: {str(e)}"}
    
    @staticmethod
    async def generate_questions(db: Session, document_id: int, count: int = 5) -> Dict[str, Any]:
        """
        문서 기반 문제 생성
        
        Args:
            db: 데이터베이스 세션
            document_id: 문서 ID
            count: 생성할 문제 수
            
        Returns:
            생성된 문제
        """
        try:
            # 문서 조회
            pdf_file = db.query(PDFFile).filter(PDFFile.id == document_id).first()
            if not pdf_file:
                return {"success": False, "error": "문서를 찾을 수 없습니다"}
            
            # 파일 경로 확인
            file_path = pdf_file.file_path
            if not os.path.exists(file_path):
                return {"success": False, "error": "파일을 찾을 수 없습니다"}
            
            # 문제 생성 실행
            logger.info(f"문제 생성 시작: {document_id}, 파일: {file_path}")
            result = pdf_ai_service.generate_exam(file_path, count)
            
            if not result.get("success", False):
                error_msg = result.get("error", "알 수 없는 오류")
                logger.error(f"문제 생성 실패: {error_msg}")
                return result
            
            # 문제 생성 결과 반환
            logger.info(f"문제 생성 완료: {document_id}")
            return {
                "success": True,
                "document_id": document_id,
                "document_name": pdf_file.filename,
                "questions": result["questions"],
                "count": count,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"문제 생성 실패: {str(e)}", exc_info=True)
            return {"success": False, "error": f"문제 생성 중 오류 발생: {str(e)}"}
            
    @staticmethod
    async def process_and_embed_document(db: Session, document_id: int) -> Dict[str, Any]:
        """
        문서 처리 및 임베딩 생성 - PDF 처리 워크플로우 통합
        
        Args:
            db: 데이터베이스 세션
            document_id: 문서 ID
            
        Returns:
            처리 결과
        """
        try:
            # 기존 PDFProcessor 로직 유지 (청킹과 임베딩은 기존 방식으로)
            result = await PDFProcessor.process_and_embed_document(db, document_id)
            
            # 이미 정의된 프로세서가 있으므로, 기존 로직을 유지하고 LangGraph 통합은 별도 기능으로 제공
            return result
        
        except Exception as e:
            logger.error(f"문서 처리 및 임베딩 실패: {str(e)}", exc_info=True)
            return {"success": False, "error": f"문서 처리 및 임베딩 중 오류 발생: {str(e)}"}
        
    @staticmethod
    async def search_similar_chunks(
        db: Session, 
        user_id: int,
        document_id: int, 
        query_text: str, 
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        """쿼리와 유사한 청크 검색 - ChromaDB 사용"""
        from app.services.pdf_agent.chromadb_service import ChromaDBService
        
        chromadb_service = ChromaDBService()
        return chromadb_service.search_similar_chunks(
            user_id=user_id,
            document_id=document_id,
            query_text=query_text,
            limit=limit
        )