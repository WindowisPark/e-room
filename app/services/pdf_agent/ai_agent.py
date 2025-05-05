# app/services/pdf_agent/ai_agent.py 개선사항

from typing import Dict, List, Any, Optional
import logging
from datetime import datetime
from sqlalchemy.orm import Session
import json

from app.models.tag import PDFFile
from app.services.pdf_agent.processor import PDFProcessor
from app.services.pdf_agent.embedding_service import EmbeddingService
from app.core.config import settings

logger = logging.getLogger(__name__)

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
            from openai import AsyncOpenAI
            
            # OpenAI 클라이언트 초기화
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
        문서 요약 생성
        
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
            
            # DB에서 문서 청크 목록 조회
            query = """
                SELECT 
                    text,
                    chunk_index,
                    start_char,
                    end_char
                FROM document_chunks
                WHERE document_id = :document_id
                ORDER BY chunk_index
            """
            
            chunks = db.execute(query, {"document_id": document_id}).fetchall()
            
            if not chunks:
                # 청크가 없으면 문서 처리 수행
                process_result = await PDFProcessor.process_and_embed_document(db, document_id)
                if not process_result.get("success"):
                    return process_result
                
                # 다시 청크 조회
                chunks = db.execute(query, {"document_id": document_id}).fetchall()
                
                if not chunks:
                    return {"success": False, "error": "문서 처리는 성공했지만 청크를 찾을 수 없습니다"}
            
            # 청크 텍스트 추출
            chunk_texts = [chunk.text for chunk in chunks]
            
            # OpenAI 클라이언트 초기화
            from openai import AsyncOpenAI
            client = AsyncOpenAI(api_key=settings.AI_API_KEY)
            
            # 요약 수준에 따른 지시사항 조정
            length_instruction = ""
            if level == "short":
                length_instruction = "간결하게 1-2문단으로 요약하세요."
            elif level == "detailed":
                length_instruction = "주요 내용을 포함하여 3-4문단으로 상세히 요약하세요."
            else:
                length_instruction = "적절한 길이로 주요 내용을 요약하세요."
            
            # 청크를 섹션으로 나누어 처리
            summaries = []
            
            # 청크 수에 따라 전략 결정
            if len(chunk_texts) <= 3:
                # 청크가 적으면 한 번에 처리
                combined_text = "\n\n".join([f"섹션 {i+1}:\n{text}" for i, text in enumerate(chunk_texts)])
                
                prompt = f"""
                다음 문서 내용을 요약해주세요. {length_instruction}
                
                문서:
                {combined_text}
                """
                
                response = await client.chat.completions.create(
                    model=settings.AI_MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "당신은 전문적인 문서 요약 AI 어시스턴트입니다. 주어진 내용을 정확하고 응집력 있게 요약하세요."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                
                summaries.append(response.choices[0].message.content.strip())
            else:
                # 청크가 많으면 섹션별로 나누어 처리
                section_size = min(5, max(1, len(chunk_texts) // 3))
                sections = [chunk_texts[i:i+section_size] for i in range(0, len(chunk_texts), section_size)]
                
                for i, section in enumerate(sections):
                    section_text = "\n\n".join([f"텍스트 {j+1}:\n{text}" for j, text in enumerate(section)])
                    
                    prompt = f"""
                    다음 문서 섹션을 요약해주세요. 섹션의 핵심 내용을 간략하게 요약하세요.
                    
                    섹션 {i+1}:
                    {section_text}
                    """
                    
                    response = await client.chat.completions.create(
                        model=settings.AI_MODEL_NAME,
                        messages=[
                            {"role": "system", "content": "당신은 전문적인 문서 요약 AI 어시스턴트입니다. 주어진 섹션을 정확하고 응집력 있게 요약하세요."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.3,
                        max_tokens=300
                    )
                    
                    section_summary = response.choices[0].message.content.strip()
                    summaries.append(section_summary)
                
                # 섹션별 요약을 통합
                combined_summary = "\n\n".join([f"섹션 {i+1} 요약:\n{summary}" for i, summary in enumerate(summaries)])
                
                prompt = f"""
                다음은 문서의 섹션별 요약입니다. 이를 통합하여 하나의 응집력 있는 요약을 만들어주세요. {length_instruction}
                
                {combined_summary}
                """
                
                response = await client.chat.completions.create(
                    model=settings.AI_MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "당신은 전문적인 문서 요약 AI 어시스턴트입니다. 섹션별 요약을 통합하여 하나의 응집력 있는 최종 요약을 작성하세요."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1000
                )
                
                # 최종 통합 요약으로 교체
                summaries = [response.choices[0].message.content.strip()]
            
            # 결과 반환
            return {
                "success": True,
                "document_id": document_id,
                "document_name": pdf_file.filename,
                "summary": summaries[0],
                "summary_level": level,
                "generated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"요약 생성 실패: {str(e)}", exc_info=True)
            return {"success": False, "error": f"요약 생성 중 오류 발생: {str(e)}"}