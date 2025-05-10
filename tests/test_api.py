# tests/test_api.py

import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import os
import sys
from typing import Optional
import shutil

# 모듈 경로 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.pdf_agent.ai_service import PDFAIService

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# AI 서비스 초기화
pdf_ai_service = PDFAIService()

# test.pdf 경로 설정
default_pdf_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'app', 'services', 'pdf_agent', 'test.pdf'))

@app.post("/api/v1/pdf-processing")
async def process_pdf(
    file: Optional[UploadFile] = File(None),
    use_default: bool = Query(False, description="기본 test.pdf 파일 사용")
):
    """PDF 파일 처리 테스트 엔드포인트"""
    try:
        if use_default:
            # 기본 PDF 사용
            pdf_path = default_pdf_path
            cleanup_needed = False
        elif file:
            # 업로드된 파일 사용
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                shutil.copyfileobj(file.file, temp_file)
                pdf_path = temp_file.name
            cleanup_needed = True
        else:
            raise HTTPException(status_code=400, detail="파일을 업로드하거나 use_default를 true로 설정해주세요")
        
        # PDF 처리
        result = pdf_ai_service.process_pdf(pdf_path)
        
        # 임시 파일 삭제
        if cleanup_needed:
            os.unlink(pdf_path)
        
        # 결과 반환
        if result.get("success", False):
            return {
                "success": True,
                "result": result["result"],
                "message": "PDF 처리 완료"
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "PDF 처리 실패"))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/generate-questions")
async def generate_questions(
    file: Optional[UploadFile] = File(None),
    use_default: bool = Query(False, description="기본 test.pdf 파일 사용"),
    count: int = Form(5)
):
    """문제 생성 테스트 엔드포인트"""
    try:
        if use_default:
            # 기본 PDF 사용
            pdf_path = default_pdf_path
            cleanup_needed = False
        elif file:
            # 업로드된 파일 사용
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                shutil.copyfileobj(file.file, temp_file)
                pdf_path = temp_file.name
            cleanup_needed = True
        else:
            raise HTTPException(status_code=400, detail="파일을 업로드하거나 use_default를 true로 설정해주세요")
        
        # 문제 생성
        result = pdf_ai_service.generate_exam(pdf_path, count)
        
        # 임시 파일 삭제
        if cleanup_needed:
            os.unlink(pdf_path)
        
        # 결과 반환
        if result.get("success", False):
            return {
                "success": True,
                "questions": result["questions"],
                "message": "문제 생성 완료"
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error", "문제 생성 실패"))
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    """루트 경로 테스트"""
    return {"message": "PDF AI 서비스 테스트 API 작동 중", "default_pdf_path": default_pdf_path}

if __name__ == "__main__":
    print(f"기본 PDF 경로: {default_pdf_path}")
    uvicorn.run(app, host="0.0.0.0", port=8000)