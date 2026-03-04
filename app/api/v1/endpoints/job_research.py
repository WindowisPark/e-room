# app/api/v1/endpoints/job_research.py

import asyncio
import logging
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.models.job_research import SavedCompany
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Pydantic Schemas ─────────────────────────────────────────────────────────

class AnalyzeRequest(BaseModel):
    url: Optional[str] = None
    text: Optional[str] = None  # 공고 텍스트 직접 입력


class SaveRequest(BaseModel):
    company_name: str
    job_title: Optional[str] = None
    source_url: Optional[str] = None
    raw_content: Optional[str] = None
    analysis: Optional[Dict[str, Any]] = None


class SavedCompanyOut(BaseModel):
    id: int
    user_id: int
    company_name: str
    job_title: Optional[str]
    source_url: Optional[str]
    analysis: Optional[Dict[str, Any]]
    created_at: Any

    class Config:
        from_attributes = True


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _scrape_url_sync(url: str) -> str:
    """URL에서 텍스트 추출 (동기). asyncio.to_thread에서 호출."""
    try:
        import httpx
        from bs4 import BeautifulSoup
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = httpx.get(url, headers=headers, timeout=15, follow_redirects=True)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)[:8000]
    except Exception as e:
        logger.warning(f"URL 스크래핑 실패 ({url}): {e}")
        return ""


def _analyze_with_ai_sync(content: str) -> Dict[str, Any]:
    """Gemini로 채용 공고 분석 (동기). asyncio.to_thread에서 호출."""
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        import json

        llm = ChatGoogleGenerativeAI(
            model=settings.AI_MODEL_NAME,
            google_api_key=settings.GOOGLE_API_KEY,
            request_timeout=settings.AI_LLM_TIMEOUT,
        )

        prompt = f"""다음 채용 공고를 분석하여 아래 JSON 형식으로 정리해주세요. 모든 필드를 한국어로 작성하세요.

채용 공고:
{content[:6000]}

응답 형식 (JSON만 출력):
{{
  "company_name": "회사명",
  "job_title": "채용 직무",
  "overview": "회사 및 직무 개요 (3~5문장)",
  "tech_stack": ["기술1", "기술2", "기술3"],
  "requirements": ["자격요건1", "자격요건2"],
  "preferred": ["우대사항1", "우대사항2"],
  "culture": "조직 문화 및 복지 요약",
  "interview_questions": [
    "예상 면접 질문1",
    "예상 면접 질문2",
    "예상 면접 질문3"
  ]
}}"""

        response = llm.invoke(prompt)
        text = response.content.strip()
        if text.startswith("```"):
            text = text.strip("`").strip()
            if text.lower().startswith("json"):
                text = text[4:].strip()
        return json.loads(text)

    except Exception as e:
        logger.error(f"AI 분석 실패: {e}")
        return {
            "company_name": "",
            "job_title": "",
            "overview": "분석에 실패했습니다. 직접 내용을 확인해주세요.",
            "tech_stack": [],
            "requirements": [],
            "preferred": [],
            "culture": "",
            "interview_questions": []
        }


# ─── Routes ───────────────────────────────────────────────────────────────────

@router.post("/analyze")
async def analyze_job(
    data: AnalyzeRequest,
    current_user: User = Depends(deps.get_current_user)
):
    """URL 또는 텍스트 → AI 분석 (저장 없이 즉시 반환)"""
    if not data.url and not data.text:
        raise HTTPException(status_code=400, detail="url 또는 text 중 하나를 입력해주세요.")

    raw = ""
    if data.url:
        raw = await asyncio.to_thread(_scrape_url_sync, data.url)
    if data.text:
        raw = (raw + "\n" + data.text).strip() if raw else data.text

    if not raw:
        raise HTTPException(status_code=422, detail="공고 내용을 가져올 수 없습니다. 텍스트를 직접 입력해주세요.")

    analysis = await asyncio.to_thread(_analyze_with_ai_sync, raw)
    return {"raw_content": raw, "analysis": analysis}


@router.post("/save", response_model=SavedCompanyOut, status_code=status.HTTP_201_CREATED)
def save_company(
    data: SaveRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    company = SavedCompany(
        user_id=current_user.id,
        company_name=data.company_name,
        job_title=data.job_title,
        source_url=data.source_url,
        raw_content=data.raw_content,
        analysis=data.analysis,
    )
    db.add(company)
    db.commit()
    db.refresh(company)
    return company


@router.get("", response_model=List[SavedCompanyOut])
def list_companies(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    return db.query(SavedCompany).filter(
        SavedCompany.user_id == current_user.id
    ).order_by(SavedCompany.created_at.desc()).all()


@router.get("/{company_id}", response_model=SavedCompanyOut)
def get_company(
    company_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    company = db.query(SavedCompany).filter(
        SavedCompany.id == company_id,
        SavedCompany.user_id == current_user.id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="기업 정보를 찾을 수 없습니다.")
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_company(
    company_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    company = db.query(SavedCompany).filter(
        SavedCompany.id == company_id,
        SavedCompany.user_id == current_user.id
    ).first()
    if not company:
        raise HTTPException(status_code=404, detail="기업 정보를 찾을 수 없습니다.")
    db.delete(company)
    db.commit()
