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
from app.services.pdf_agent.chromadb_service import ChromaDBService

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
            # HTTP URL을 S3 URI로 변환하고 boto3를 사용하여 다운로드
            logger.info(f"S3 파일 다운로드 시작 (boto3 with HTTP URL): {file_path}")
            
            from app.core.config import settings
            import boto3
            from botocore.client import Config
            from urllib.parse import urlparse
            
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            temp_path = temp_file.name
            temp_file.close()
            
            try:
                # URL에서 버킷 이름과 객체 키 추출
                parsed_url = urlparse(file_path)
                bucket_name = "ai-agent-pdf-storage"  # 고정된 버킷 이름 사용
                
                # URL 경로에서 객체 키 추출
                if "amazonaws.com" in parsed_url.netloc:
                    # ai-agent-pdf-storage.s3.amazonaws.com/users/1/study/...
                    object_key = parsed_url.path.lstrip('/')
                else:
                    # 다른 형태의 URL
                    object_key = '/'.join(parsed_url.path.split('/')[2:])  # 버킷 이름 이후 경로
                
                logger.info(f"S3 다운로드 정보: 버킷={bucket_name}, 키={object_key}")
                
                # S3 클라이언트 생성
                s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY,
                    aws_secret_access_key=settings.AWS_SECRET_KEY,
                    region_name=settings.AWS_REGION,
                    config=Config(signature_version='s3v4')
                )
                
                # 파일이 존재하는지 확인하지 않고 바로 다운로드 시도
                s3_client.download_file(bucket_name, object_key, temp_path)
                logger.info(f"S3 파일 다운로드 완료: {file_path} -> {temp_path}")
                file_path = temp_path
                
            except Exception as download_err:
                try:
                    os.unlink(temp_path)
                except:
                    pass
                logger.error(f"S3 파일 다운로드 실패: {str(download_err)}")
                
                # 대체 방식: 직접 HTTP 요청 시도 (단, 공개 액세스 가능한 파일만)
                try:
                    logger.info(f"대체 방식으로 다운로드 시도: {file_path}")
                    import requests
                    response = requests.get(file_path, stream=True)
                    response.raise_for_status()
                    
                    with open(temp_path, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)
                            
                    logger.info(f"대체 방식으로 다운로드 성공: {file_path} -> {temp_path}")
                    file_path = temp_path
                except Exception as alt_err:
                    logger.error(f"대체 방식 다운로드 실패: {str(alt_err)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"S3 파일 다운로드 실패: {str(download_err)}, 대체 방식도 실패: {str(alt_err)}"
                    )
        elif not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"파일을 찾을 수 없습니다: {file_path}")

        # 상태 초기화
        state = {
            "user_id": str(current_user.id),
            "document_id": document_id,  # 정수 값으로 전달
            "pdf_path": file_path,
            "purpose": "preprocessing",
            "folder": "default"
        }

        logger.info(f"초기 상태 생성: {state}")
        graph = get_processing_graph()
        result = graph.invoke(state)
        # 로깅 추가
        logger.info(f"문서 처리 완료 - 결과 키: {list(result.keys() if isinstance(result, dict) else [])}")

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
        # 상태 값이 누락되는 문제 해결
        # 크로마DB에 직접 문서 존재 여부 확인
        chroma_service = ChromaDBService()
        embedding_stored = chroma_service.check_document_exists(int(current_user.id), document_id)
        
        # 청크 수는 실제 저장된 청크 수를 조회
        chunks_count = chroma_service.count_document_chunks(int(current_user.id), document_id)
        
        logger.info(f"실제 ChromaDB 확인 결과: embedding_stored={embedding_stored}, chunks_count={chunks_count}")

        return {
            "success": True,
            "document_id": document.id,
            "document_name": document.filename,
            "message": "문서 처리가 완료되었습니다.",
            "embedding_stored": embedding_stored,  # 실제 DB에서 확인한 결과 사용
            "chunks_count": chunks_count,          # 실제 DB에서 확인한 결과 사용
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

@router.post("/ask", response_model=Dict[str, Any])
async def ask_question(
    query: str = Body(..., description="사용자 질문"),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """
    사용자 질문을 받아 적절한 처리를 수행하는 통합 API
    1. 질문 분석 (요약, Q&A, 문제 생성 등)
    2. 관련 문서 검색
    3. 해당 요구사항에 맞는 처리 수행
    """
    try:
        # 1. 질문 분석하여 목적 파악
        from app.services.pdf_agent.nodes.common import judge_the_purpose_of_the_input
        
        # 임시 상태 생성
        temp_state = {
            "user_id": str(current_user.id),
            "last_user_query": query
        }
        
        # 목적 판단
        purpose_state = judge_the_purpose_of_the_input(temp_state)
        purpose = purpose_state.get("purpose", "qa_system")  # 기본값은 Q&A
        
        logger.info(f"질문 목적 분석 결과: {purpose}")
        
        # 2. 관련 문서 검색 (ChromaDB 유사도 검색)
        chroma_service = ChromaDBService()
        folder_name = "default"  # 기본 폴더

        # DB와 폴더 경로 로깅
        db_path = chroma_service.db_path if hasattr(chroma_service, 'db_path') else "Unknown"
        logger.info(f"ChromaDB 경로: {db_path}")
        logger.info(f"사용자 ID: {current_user.id}, 폴더: {folder_name}")
        
        # 이 부분에서 실패하면 자세한 오류 로깅
        try:
            relevant_docs = chroma_service.search_across_documents(
                user_id=current_user.id,
                query_text=query,
                limit=5  # 상위 5개 결과만
            )
            logger.info(f"관련 문서 검색 결과: {len(relevant_docs)}개 문서 찾음")
            for i, doc in enumerate(relevant_docs[:2]):  # 처음 2개만 로깅
                logger.info(f"  문서 {i+1}: ID={doc.get('document_id')}, 유사도={doc.get('similarity')}")
        except Exception as search_err:
            logger.error(f"문서 검색 중 오류: {str(search_err)}", exc_info=True)
            relevant_docs = []
        
        if not relevant_docs:
            logger.warning("질문과 관련된 문서를 찾을 수 없음")
            return {
                "success": False,
                "message": "질문과 관련된 문서를 찾을 수 없습니다.",
                "query": query,
                "purpose": purpose
            }
        
        # 사용자의 모든 문서를 대상으로 검색
        relevant_docs = chroma_service.search_across_documents(
            user_id=current_user.id,
            query_text=query,
            limit=5  # 상위 5개 결과만
        )
        
        if not relevant_docs:
            return {
                "success": False,
                "message": "질문과 관련된 문서를 찾을 수 없습니다.",
                "query": query,
                "purpose": purpose
            }
        
        # 가장 관련성 높은 문서 선택
        best_match = relevant_docs[0]
        document_id = best_match["document_id"]
        
        # 문서 정보 조회
        document = db.query(PDFFile).filter(PDFFile.id == document_id).first()
        if not document:
            return {
                "success": False,
                "message": "문서를 찾을 수 없습니다.",
                "query": query,
                "purpose": purpose
            }
        
        # 3. 목적에 따른 적절한 처리 수행
        result = None
        
        if purpose == "summary":
            # 요약 처리
            result = await summarize_document(
                document_id=document_id,
                level="default",
                db=db,
                current_user=current_user
            )
            result["answer_type"] = "summary"
            
        elif purpose == "generate_exam":
            # 문제 생성
            result = await generate_questions(
                document_id=document_id,
                count=5,
                db=db,
                current_user=current_user
            )
            result["answer_type"] = "questions"
            
        else:  # qa_system 또는 기타
            # 질의응답
            result = await query_document(
                document_id=document_id,
                query=query,
                db=db,
                current_user=current_user
            )
            result["answer_type"] = "qa"
        
        # 4. 통합 응답 구성
        response = {
            "success": True,
            "query": query,
            "purpose": purpose,
            "document_id": document_id,
            "document_name": document.filename,
            **result  # 각 처리 결과 통합
        }
        
        return response
        
    except Exception as e:
        logger.error(f"질문 처리 중 오류 발생: {str(e)}", exc_info=True)
        return {
            "success": False,
            "message": f"처리 중 오류가 발생했습니다: {str(e)}",
            "query": query
        }