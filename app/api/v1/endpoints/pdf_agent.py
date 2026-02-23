from fastapi import APIRouter, Depends, HTTPException, Query, Body, UploadFile, File
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional, List
import asyncio
import hashlib
import json
import logging
import os
import tempfile
from urllib.parse import urlparse
import boto3
from botocore.client import Config

from app.core.config import settings
from app.models.user import User
from app.api import deps
from app.services.pdf_agent.graphs.main import get_processing_graph
from app.services.pdf_agent.graphs.qa_graph import get_qa_graph
from app.services.pdf_agent.graphs.summary_graph import get_summary_graph
from app.services.pdf_agent.graphs.exam_graph import get_exam_graph
from app.services.pdf_agent.graphs.schedule_graph import get_schedule_graph
from app.services.pdf_agent.chromadb_service import ChromaDBService
from app.services.pdf_agent.nodes.common import judge_the_purpose_of_the_input
from app.services.pdf_agent.tools import get_initial_state
from app.services.cache_service import CacheService

router = APIRouter()
_cache = CacheService()
_AI_ASK_TTL = 3600
logger = logging.getLogger(__name__)


@router.post("/process", response_model=Dict[str, Any])
async def process_document(
    document_id: int = Body(..., description="문서 ID"),
    file_path: str = Body("", description="파일 경로 또는 URL"),
    upload_file: UploadFile = File(None),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    temp_path = None
    try:
        is_http_url = file_path.startswith("http://") or file_path.startswith("https://")
        parsed_url = urlparse(file_path) if is_http_url else None

        if upload_file:
            temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
            with open(temp_path, "wb") as f:
                f.write(await upload_file.read())
            file_path = temp_path
        elif is_http_url and "amazonaws.com" in parsed_url.netloc:
            if not settings.S3_BUCKET_NAME:
                raise HTTPException(status_code=500, detail="S3 버킷이 설정되지 않았습니다")
            bucket_name = settings.S3_BUCKET_NAME
            object_key = parsed_url.path.lstrip('/')
            temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
            s3 = boto3.client(
                "s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY,
                aws_secret_access_key=settings.AWS_SECRET_KEY,
                region_name=settings.AWS_REGION,
                config=Config(signature_version='s3v4')
            )
            s3.download_file(bucket_name, object_key, temp_path)
            file_path = temp_path
        elif not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {file_path}")

        state = {
            "user_id": str(current_user.id),
            "document_id": document_id,
            "pdf_path": file_path,
            "folder": "default",
            "purpose": "preprocessing"
        }

        logger.info(f"초기 상태: {state}")
        graph = get_processing_graph()
        result = await asyncio.to_thread(graph.invoke, state)

        if result.get("error"):
            raise HTTPException(status_code=500, detail=f"문서 처리 실패: {result['error']}")

        chroma = ChromaDBService()
        embedding_stored = chroma.check_document_exists(int(current_user.id), document_id)
        chunks_count = chroma.count_document_chunks(int(current_user.id), document_id)

        return {
            "success": True,
            "document_id": document_id,
            "message": "문서 처리가 완료되었습니다.",
            "embedding_stored": embedding_stored,
            "chunks_count": chunks_count
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"문서 처리 실패: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"문서 처리 중 오류: {str(e)}")
    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)


@router.post("/ask", response_model=Dict[str, Any])
async def ask_question(
    query: str = Body(..., description="사용자 질문 또는 요청"),
    generate_pdf: bool = Body(False, description="요약일 경우 PDF 생성 여부"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    cache_key = hashlib.sha256(f"{current_user.id}:{query}".encode()).hexdigest()
    cached = _cache.get_json(cache_key, prefix="ai_ask")
    if cached:
        logger.info(f"/ask 캐시 히트: user={current_user.id}")
        return cached

    try:
        temp_state = {"user_id": str(current_user.id), "last_user_query": query}
        purpose_state = await asyncio.to_thread(judge_the_purpose_of_the_input, temp_state)
        purpose = purpose_state.get("purpose", "qa_system")
        logger.info(f"판단된 목적: {purpose}")

        state = get_initial_state(
            user_id=str(current_user.id),
            purpose=purpose,
            query=query
        )

        if purpose == "summary":
            graph = get_summary_graph()
        elif purpose == "generate_exam":
            graph = get_exam_graph()
        elif purpose == "schedule":
            graph = get_schedule_graph()
        else:
            graph = get_qa_graph()

        result = await asyncio.to_thread(graph.invoke, state)
        answer = result.get("result") or result.get("last_assistant_response") or "응답 생성 실패"

        response_data = {
            "success": True,
            "query": query,
            "purpose": purpose,
            "answer": answer,
            **{k: v for k, v in result.items() if k not in ["answer"]}
        }
        _cache.set_json(cache_key, response_data, ttl=_AI_ASK_TTL, prefix="ai_ask")
        return response_data

    except Exception as e:
        logger.error(f"/ask 처리 중 오류: {str(e)}", exc_info=True)
        return {"success": False, "message": f"처리 중 오류: {str(e)}", "query": query}


@router.post("/exam", response_model=Dict[str, Any])
async def generate_exam_without_previous(
    count: int = Query(5, ge=1, le=20),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    try:
        state = {
            "user_id": str(current_user.id),
            "folder": "default",
            "purpose": "generate_exam",
            "query": f"{count}개 시험 문제 생성",
            "previous_exam_path": [],
            "previous_exam_index": 0,
            "personality": {},
            "question_count": count
        }

        graph = get_exam_graph()
        result = await asyncio.to_thread(graph.invoke, state)

        return {
            "success": True,
            "questions": result.get("result", ""),
            "personality_analysis": result.get("final_personality", "")
        }

    except Exception as e:
        logger.error(f"문제 생성 실패: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="문제 생성 실패")


@router.post("/schedule", response_model=Dict[str, Any])
async def generate_schedule_without_doc(
    subjects: List[str] = Body(...),
    importance: List[str] = Body(...),
    deadlines: List[str] = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    try:
        state = {
            "user_id": str(current_user.id),
            "folder": "default",
            "subjects": subjects,
            "importance": importance,
            "deadlines": deadlines,
            "subject_index": 0,
            "final_index": [],
            "messages": []
        }

        graph = get_schedule_graph()
        result = await asyncio.to_thread(graph.invoke, state)

        if "schedule" not in result:
            raise HTTPException(status_code=500, detail="학습 계획 생성 실패")

        return {"success": True, "schedule": result["schedule"]}

    except Exception as e:
        logger.error(f"스케줄 생성 실패: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="스케줄 생성 중 오류")
