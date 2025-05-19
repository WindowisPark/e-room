# test_pdf_agent.py
import asyncio
import os
import sys
import json
from datetime import datetime

# 프로젝트 루트 경로 추가
sys.path.append('.')

from app.db.session import SessionLocal
from app.services.pdf_agent.processor import PDFProcessor
from app.services.pdf_agent.embedding_service import EmbeddingService
from app.models.tag import PDFFile

async def test_process_and_embed_document():
    """문서 처리 및 임베딩 생성 테스트"""
    db = SessionLocal()

    try:
        # 테스트할 문서 ID (실제 DB에 존재하는 PDF 문서 ID)
        document_id = 1  # 테스트 환경에 맞게 변경

        print(f"문서 ID {document_id} 처리 시작...")
        result = await PDFProcessor.process_and_embed_document(db, document_id)

        print("처리 결과:")
        print(json.dumps(result, indent=2, ensure_ascii=False))

        return result
    finally:
        db.close()

async def test_query_document():
    """문서 질의응답 테스트"""
    db = SessionLocal()

    try:
        # 테스트할 문서 ID와 질문 (실제 DB에 존재하는 PDF 문서 ID)
        document_id = 1  # 테스트 환경에 맞게 변경
        query = "이 문서의 주요 내용은 무엇인가요?"  # 테스트 질문

        # 임베딩 서비스 초기화
        embedding_service = EmbeddingService()

        print(f"문서 ID {document_id}에 대한 질문: '{query}'")

        # 유사한 청크 검색
        similar_chunks = await embedding_service.search_similar_chunks_async(
            db=db,
            document_id=document_id,
            query_text=query,
            limit=5
        )

        print(f"검색된 유사 청크: {len(similar_chunks)}개")

        if not similar_chunks:
            print("유사한 청크를 찾을 수 없습니다.")
            return {"success": False, "error": "유사한 청크를 찾을 수 없습니다."}

        # 각 청크의 유사도 출력
        for i, chunk in enumerate(similar_chunks):
            print(f"청크 {i+1} (유사도: {chunk.get('similarity', 0):.4f}):")
            print(f"  {chunk['text'][:100]}...")

        # 유사 청크들로 컨텍스트 구성
        contexts = [chunk["text"] for chunk in similar_chunks]

        # AI 모델로 답변 생성
        from app.services.pdf_agent.ai_agent import PDFAgent
        answer = await PDFAgent.generate_answer(query, contexts)

        print("\n생성된 답변:")
        print(answer)

        return {
            "success": True,
            "query": query,
            "answer": answer,
            "chunks": similar_chunks
        }
    finally:
        db.close()

async def main():
    """테스트 메인 함수"""
    # 순차적으로 테스트 실행
    await test_process_and_embed_document()
    await test_query_document()

if __name__ == "__main__":
    asyncio.run(main())