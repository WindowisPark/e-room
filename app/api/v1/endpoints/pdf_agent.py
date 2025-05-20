# app/api/v1/endpoints/pdf_agent.py

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Dict, Any, Optional
import logging
import os

from app.api import deps
from app.models.user import User
from app.models.tag import PDFFile
from app.services.pdf_agent.tools import get_initial_state
from app.services.pdf_agent.graphs.main import get_processing_graph
from app.services.pdf_agent.graphs.qa_graph import get_qa_graph
from app.services.pdf_agent.graphs.summary_graph import get_summary_graph
from app.services.pdf_agent.graphs.exam_graph import get_exam_graph

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/{document_id}/process", response_model=Dict[str, Any])
async def process_document(
    document_id: int = Path(..., title="PDF 문서 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """LangGraph 기반 PDF 문서 처리 (전처리 + 벡터 저장 등 포함)"""
    document = db.query(PDFFile).filter(PDFFile.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    if not document.team_id and document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")

    if document.team_id:
        from app.services.team_service import check_team_permission
        has_access = await check_team_permission(db=db, team_id=document.team_id, user_id=current_user.id)
        if not has_access:
            raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")

    try:
        from urllib.parse import urlparse
        import tempfile
        import os
        import requests

        file_path = document.file_path
        parsed_url = urlparse(file_path)
        is_http_s3_url = file_path.startswith("http://") or file_path.startswith("https://")
        is_s3_uri = parsed_url.scheme == "s3" or "amazonaws.com" in parsed_url.netloc

        temp_path = None

        if is_s3_uri and not is_http_s3_url:
            # boto3 방식 S3 다운로드
            from app.core.config import settings
            import boto3
            from botocore.client import Config

            logger.info(f"S3 파일 다운로드 시작 (boto3): {file_path}")

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_path = temp_file.name
            temp_file.close()

            try:
                bucket_name = parsed_url.netloc.split('.')[0]
                object_key = parsed_url.path.lstrip('/')

                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY,
                    aws_secret_access_key=settings.AWS_SECRET_KEY,
                    region_name=settings.AWS_REGION,
                    config=Config(signature_version='s3v4')
                )

                s3_client.download_file(bucket_name, object_key, temp_path)
                logger.info(f"S3 파일 다운로드 완료: {file_path} -> {temp_path}")
                file_path = temp_path
            except Exception as e:
                try:
                    os.unlink(temp_path)
                except:
                    pass
                logger.error(f"S3 다운로드 실패: {e}")
                raise HTTPException(status_code=500, detail="S3 파일 다운로드 실패")

        elif is_http_s3_url:
            # signed/public URL 다운로드 (requests 사용)
            logger.info(f"S3 파일 다운로드 시작 (requests): {file_path}")

            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_path = temp_file.name
            temp_file.close()

            try:
                response = requests.get(file_path, stream=True)
                response.raise_for_status()

                with open(temp_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                logger.info(f"S3 파일 다운로드 완료: {file_path} -> {temp_path}")
                file_path = temp_path
            except Exception as download_err:
                try:
                    os.unlink(temp_path)
                except:
                    pass
                logger.error(f"S3 파일 다운로드 실패: {str(download_err)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"S3 파일 다운로드 실패: {str(download_err)}"
                )

        elif not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {file_path}")

        # 상태 초기화
        state = get_initial_state(
            user_id=str(current_user.id),
            document_id=int(document_id),
            pdf_path=file_path,
            purpose="preprocessing",
            folder="default"
        )

        logger.info(f"PDF 처리 시작: document_id={document_id}, file_path={file_path}")
        graph = get_processing_graph()
        result = graph.invoke(state)

        # 임시 파일 삭제
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                logger.info(f"임시 파일 삭제 완료: {temp_path}")
            except Exception as del_err:
                logger.warning(f"임시 파일 삭제 실패: {str(del_err)}")

        if result.get("error"):
            logger.error(f"PDF 처리 실패: {result.get('error')}")
            raise HTTPException(
                status_code=500, 
                detail=f"문서 처리 중 오류 발생: {result.get('error')}"
            )

        return {
            "success": True,
            "document_id": document.id,
            "document_name": document.filename,
            "message": "문서 처리가 완료되었습니다.",
            "embedding_stored": result.get("embedding_stored", False),
            "chunks_count": len(result.get("doc_chunks", [])),
            "error": result.get("error")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF Agent 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"문서 처리 중 오류 발생: {str(e)}")


@router.post("/{document_id}/query", response_model=Dict[str, Any])
async def query_document(
    document_id: int = Path(..., title="PDF 문서 ID"),
    query: str = Body(..., description="질문 내용"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    document = db.query(PDFFile).filter(PDFFile.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    if not document.team_id and document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")

    if document.team_id:
        from app.services.team_service import check_team_permission
        has_access = await check_team_permission(db=db, team_id=document.team_id, user_id=current_user.id)
        if not has_access:
            raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")

    try:
        state = get_initial_state(
            user_id=str(current_user.id),
            document_id=document_id,
            pdf_path=document.file_path,
            purpose="qa_system",
            query=query
        )
        graph = get_qa_graph()
        result = graph.invoke(state)

        answer = result.get("last_assistant_response", "응답을 생성하지 못했습니다.")

        return {
            "success": True,
            "document_id": document_id,
            "document_name": document.filename,
            "query": query,
            "answer": answer
        }

    except Exception as e:
        logger.error(f"질의응답 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"질문 처리 중 오류 발생: {str(e)}")


@router.post("/{document_id}/summarize", response_model=Dict[str, Any])
async def summarize_document(
    document_id: int = Path(..., title="PDF 문서 ID"),
    level: str = Query("default", description="요약 수준 (default, short, detailed)"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    document = db.query(PDFFile).filter(PDFFile.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    if not document.team_id and document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")

    if document.team_id:
        from app.services.team_service import check_team_permission
        has_access = await check_team_permission(db=db, team_id=document.team_id, user_id=current_user.id)
        if not has_access:
            raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")

    try:
        query_str = f"이 문서를 {level} 수준으로 요약해주세요"
        state = get_initial_state(
            user_id=str(current_user.id),
            document_id=document_id,
            pdf_path=document.file_path,
            purpose="summary",
            query=query_str
        )
        state["summary_level"] = level

        graph = get_summary_graph()
        result = graph.invoke(state)

        summary = result.get("result", "") or result.get("last_assistant_response", "요약을 생성하지 못했습니다.")

        return {
            "success": True,
            "document_id": document_id,
            "document_name": document.filename,
            "level": level,
            "summary": summary
        }

    except Exception as e:
        logger.error(f"요약 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"요약 처리 중 오류 발생: {str(e)}")


@router.post("/{document_id}/questions", response_model=Dict[str, Any])
async def generate_questions(
    document_id: int = Path(..., title="PDF 문서 ID"),
    count: int = Query(5, description="생성할 문제 수", ge=1, le=20),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    document = db.query(PDFFile).filter(PDFFile.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")

    if not document.team_id and document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")

    if document.team_id:
        from app.services.team_service import check_team_permission
        has_access = await check_team_permission(db=db, team_id=document.team_id, user_id=current_user.id)
        if not has_access:
            raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")

    try:
        query_str = f"이 문서에서 {count}개의 시험 문제를 만들어주세요"
        state = get_initial_state(
            user_id=str(current_user.id),
            document_id=document_id,
            pdf_path=document.file_path,
            purpose="generate_exam",
            query=query_str
        )
        state["question_count"] = count

        graph = get_exam_graph()
        result = graph.invoke(state)

        questions = result.get("result", "") or result.get("last_assistant_response", "문제를 생성하지 못했습니다.")

        return {
            "success": True,
            "document_id": document_id,
            "document_name": document.filename,
            "count": count,
            "questions": questions
        }

    except Exception as e:
        logger.error(f"문제 생성 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"문제 생성 중 오류 발생: {str(e)}")
