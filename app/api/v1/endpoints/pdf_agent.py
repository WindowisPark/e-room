# app/api/v1/endpoints/pdf_agent.py

from fastapi import APIRouter, Depends, HTTPException, Query, Path, Body
from sqlalchemy.orm import Session
from typing import Dict, Any
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
from app.services.pdf_agent.chromadb_service import ChromaDBService

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/{document_id}/process", response_model=Dict[str, Any])
async def process_document(
    document_id: int = Path(..., title="PDF 문서 ID"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """LangGraph 기반 PDF 문서 처리 (gptpdf 기반 리팩토링)"""
    # 1. 문서 조회 및 권한 확인
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

    # 2. S3 또는 URL 다운로드 → 로컬 PDF 확보
    from urllib.parse import urlparse
    import requests, tempfile, boto3
    from botocore.client import Config
    from app.core.config import settings

    file_path = document.file_path
    parsed_url = urlparse(file_path)
    is_http_url = file_path.startswith("http://") or file_path.startswith("https://")
    is_s3_uri = parsed_url.scheme == "s3" or "amazonaws.com" in parsed_url.netloc

    temp_path = None
    try:
        if is_s3_uri and not is_http_url:
            bucket_name = parsed_url.netloc.split('.')[0]
            object_key = parsed_url.path.lstrip('/')
            temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
            s3 = boto3.client("s3",
                aws_access_key_id=settings.AWS_ACCESS_KEY,
                aws_secret_access_key=settings.AWS_SECRET_KEY,
                region_name=settings.AWS_REGION,
                config=Config(signature_version='s3v4')
            )
            s3.download_file(bucket_name, object_key, temp_path)
            file_path = temp_path

        elif is_http_url:
            temp_path = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf").name
            response = requests.get(file_path, stream=True)
            response.raise_for_status()
            with open(temp_path, "wb") as f:
                for chunk in response.iter_content(8192):
                    f.write(chunk)
            file_path = temp_path

        elif not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {file_path}")

        # 3. LangGraph 실행 (gptpdf 기반으로 내부 노드 구성됨)
        state = {
            "user_id": str(current_user.id),
            "document_id": document_id,
            "pdf_path": file_path,
            "folder": "default",
            "purpose": "preprocessing"
        }

        logger.info(f"초기 상태: {state}")
        graph = get_processing_graph()
        result = graph.invoke(state)

        if result.get("error"):
            raise HTTPException(status_code=500, detail=f"문서 처리 실패: {result['error']}")

        # 4. Chroma 저장 여부 확인
        chroma = ChromaDBService()
        embedding_stored = chroma.check_document_exists(int(current_user.id), document_id)
        chunks_count = chroma.count_document_chunks(int(current_user.id), document_id)

        return {
            "success": True,
            "document_id": document.id,
            "document_name": document.filename,
            "message": "문서 처리가 완료되었습니다.",
            "embedding_stored": embedding_stored,
            "chunks_count": chunks_count
        }

    finally:
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)



@router.post("/{document_id}/query", response_model=Dict[str, Any])
async def query_document(
    document_id: int = Path(..., title="PDF 문서 ID"),
    query: str = Body(..., description="질문 내용"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """문서 기반 질의응답 API - 처리되지 않은 문서면 자동 전처리"""
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
        # ✅ 사전 처리 확인: 임베딩 존재 여부 확인
        chroma = ChromaDBService()
        embedding_exists = chroma.check_document_exists(int(current_user.id), document_id)
        if not embedding_exists:
            logger.info(f"임베딩 미존재 → /process 자동 실행: document_id={document_id}")
            await process_document(document_id=document_id, db=db, current_user=current_user)

        # ✅ LangGraph 실행
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
    generate_pdf: bool = Query(False, description="요약 PDF 생성 여부"),
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
        # ✅ 전처리 보장: 임베딩 없으면 /process 실행
        from app.services.pdf_agent.chromadb_service import ChromaDBService
        chroma = ChromaDBService()
        if not chroma.check_document_exists(int(current_user.id), document_id):
            logger.info(f"요약 전처리: /process 자동 실행")
            await process_document(document_id=document_id, db=db, current_user=current_user)

        # ✅ 상태 초기화 및 summary_level 주입
        from app.services.pdf_agent.tools import get_initial_state
        state = get_initial_state(
            user_id=str(current_user.id),
            document_id=document_id,
            pdf_path=document.file_path,
            purpose="summary",
            query=f"이 문서를 {level} 수준으로 요약해주세요"
        )
        state["summary_level"] = level

        from app.services.pdf_agent.graphs.summary_graph import get_summary_graph
        result = get_summary_graph().invoke(state)

        summary = result.get("result") or result.get("last_assistant_response") or "요약 생성 실패"

        # ✅ 선택적 PDF 생성
        pdf_path = None
        if generate_pdf and summary:
            from app.services.pdf_service import PDFConverter
            pdf_title = f"{document.filename} 요약본 ({level})"
            pdf_path = PDFConverter.text_to_pdf(summary, pdf_title, current_user.id)

        response = {
            "success": True,
            "document_id": document_id,
            "document_name": document.filename,
            "level": level,
            "summary": summary,
            "pdf_generated": bool(pdf_path)
        }

        if pdf_path:
            response["pdf_path"] = pdf_path

        return response

    except Exception as e:
        logger.error(f"요약 처리 실패: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"요약 중 오류 발생: {str(e)}")



@router.post("/{document_id}/questions", response_model=Dict[str, Any])
async def generate_questions_with_upload(
    document_id: int = Path(..., title="PDF 문서 ID"),
    count: int = Query(5, description="생성할 문제 수", ge=1, le=20),
    previous_exam_files: List[UploadFile] = File(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    document = db.query(PDFFile).filter(PDFFile.id == document_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="문서를 찾을 수 없습니다")
    if not document.team_id and document.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="문서에 접근할 권한이 없습니다")

    # 임시 파일로 기출문제 저장
    import tempfile, os
    temp_paths = []
    try:
        for file in previous_exam_files:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_file.write(await file.read())
            temp_file.close()
            temp_paths.append(temp_file.name)

        # 상태 구성
        state = {
            "user_id": str(current_user.id),
            "document_id": document_id,
            "folder": "default",
            "purpose": "generate_exam",
            "query": f"{count}개 시험 문제 생성",
            "previous_exam_path": temp_paths,
            "previous_exam_index": 0,
            "personality": {},
            "question_count": count
        }

        from app.services.pdf_agent.graphs.exam_graph import get_exam_graph
        graph = get_exam_graph()
        result = graph.invoke(state)

        if result.get("error"):
            raise HTTPException(status_code=500, detail=f"시험 문제 생성 실패: {result['error']}")

        return {
            "success": True,
            "document_id": document.id,
            "document_name": document.filename,
            "questions": result.get("result", ""),
            "personality_analysis": result.get("final_personality", "")
        }

    finally:
        for path in temp_paths:
            if os.path.exists(path):
                os.unlink(path)


@router.post("/ask", response_model=Dict[str, Any])
async def ask_question(
    query: str = Body(..., description="사용자 질문"),
    generate_pdf: bool = Body(False, description="요약일 경우 PDF 생성 여부"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    try:
        from app.services.pdf_agent.nodes.common import judge_the_purpose_of_the_input
        from app.services.pdf_agent.chromadb_service import ChromaDBService

        # 1. 목적 추론
        if any(keyword in query for keyword in ["요약", "정리", "간추려", "축약", "핵심"]):
            purpose = "summary"
            logger.info(f"한국어 키워드로 목적 판단: {purpose}")
        else:
            temp_state = {"user_id": str(current_user.id), "last_user_query": query}
            purpose_state = judge_the_purpose_of_the_input(temp_state)
            purpose = purpose_state.get("purpose", "qa_system")
        logger.info(f"질문 목적 분석 결과: {purpose}")

        # 2. 사용자 문서 중 기본 문서 선택
        user_pdfs = db.query(PDFFile).filter(PDFFile.owner_id == current_user.id).all()
        if not user_pdfs:
            return {
                "success": False,
                "message": "질문에 사용할 문서가 없습니다. 먼저 PDF를 업로드해주세요.",
                "query": query
            }
        document = user_pdfs[0]
        document_id = document.id

        # 3. 문서가 처리되어 있는지 확인 → 아니면 /process 자동 실행
        chroma = ChromaDBService()
        if not chroma.check_document_exists(current_user.id, document_id):
            logger.info(f"/ask에서 문서 미처리 → /process 자동 실행")
            await process_document(document_id=document_id, db=db, current_user=current_user)

        # 4. 목적별 처리 실행
        if purpose == "summary":
            result = await summarize_document(
                document_id=document_id,
                level="default",
                generate_pdf=generate_pdf,
                db=db,
                current_user=current_user
            )
            result["answer_type"] = "summary"

        elif purpose == "generate_exam":
            result = await generate_questions_with_upload(
                document_id=document_id,
                count=5,
                previous_exam_files=[],  # /ask에서는 기출 제공 X
                db=db,
                current_user=current_user
            )
            result["answer_type"] = "questions"

        else:
            result = await query_document(
                document_id=document_id,
                query=query,
                db=db,
                current_user=current_user
            )
            result["answer_type"] = "qa"

        # 5. 최종 응답 구성
        return {
            "success": True,
            "query": query,
            "purpose": purpose,
            "document_id": document_id,
            "document_name": document.filename,
            "answer": result.get("answer", ""),
            **{k: v for k, v in result.items() if k not in ["answer"]}
        }

    except Exception as e:
        logger.error(f"/ask 처리 중 오류: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"질문 처리 중 오류 발생: {str(e)}",
            "query": query
        }

@router.post("/{document_id}/schedule", response_model=Dict[str, Any])
async def generate_schedule(
    document_id: int,
    subjects: List[str] = Body(...),
    importance: List[str] = Body(...),
    deadlines: List[str] = Body(...),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    학습 계획 생성 API
    프런트는 이 API를 통해 JSON 스케줄을 받아 캘린더에 렌더링 가능
    """
    try:
        state = {
            "user_id": str(current_user.id),
            "document_id": document_id,
            "subjects": subjects,
            "importance": importance,
            "deadlines": deadlines,
            "subject_index": 0,
            "final_index": [],
            "messages": [],
        }

        from app.services.pdf_agent.graphs.schedule_graph import get_schedule_graph
        graph = get_schedule_graph(StateGraph(dict))
        result = graph.invoke(state)

        if "schedule" not in result:
            raise HTTPException(status_code=500, detail="학습 계획 생성 실패")

        return {
            "success": True,
            "schedule": result["schedule"]  # ⬅️ 프런트에 바로 쓰이는 JSON
        }

    except Exception as e:
        logger.error(f"학습 계획 생성 오류: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"스케줄 생성 중 오류 발생: {str(e)}")
