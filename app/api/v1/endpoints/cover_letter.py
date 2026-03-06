# app/api/v1/endpoints/cover_letter.py

import asyncio
import logging
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.models.cover_letter import CoverLetter, CoverLetterItem
from app.models.resume import ResumeProfile, ResumeItem
from app.models.job_research import SavedCompany
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()


# ─── Pydantic Schemas ─────────────────────────────────────────────────────────

class CoverLetterCreate(BaseModel):
    title: str
    company_id: Optional[int] = None
    resume_profile_id: Optional[int] = None


class CoverLetterUpdate(BaseModel):
    title: Optional[str] = None
    company_id: Optional[int] = None
    resume_profile_id: Optional[int] = None


class CoverLetterOut(BaseModel):
    id: int
    user_id: int
    title: str
    company_id: Optional[int]
    resume_profile_id: Optional[int]
    created_at: Any
    updated_at: Any

    class Config:
        from_attributes = True


class CoverLetterItemCreate(BaseModel):
    question: str
    answer: Optional[str] = None
    char_limit: Optional[int] = None
    order_index: Optional[int] = 0


class CoverLetterItemUpdate(BaseModel):
    question: Optional[str] = None
    answer: Optional[str] = None
    char_limit: Optional[int] = None
    order_index: Optional[int] = None


class CoverLetterItemOut(BaseModel):
    id: int
    cover_letter_id: int
    question: str
    answer: Optional[str]
    char_limit: Optional[int]
    order_index: int

    class Config:
        from_attributes = True


class CoverLetterWithItems(CoverLetterOut):
    items: List[CoverLetterItemOut] = []


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_cl_or_404(cl_id: int, user_id: int, db: Session) -> CoverLetter:
    cl = db.query(CoverLetter).filter(
        CoverLetter.id == cl_id,
        CoverLetter.user_id == user_id
    ).first()
    if not cl:
        raise HTTPException(status_code=404, detail="자소서를 찾을 수 없습니다.")
    return cl


# ─── Cover Letter CRUD ────────────────────────────────────────────────────────

@router.get("", response_model=List[CoverLetterOut])
def list_cover_letters(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    return db.query(CoverLetter).filter(
        CoverLetter.user_id == current_user.id
    ).order_by(CoverLetter.updated_at.desc()).all()


@router.post("", response_model=CoverLetterOut, status_code=status.HTTP_201_CREATED)
def create_cover_letter(
    data: CoverLetterCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    cl = CoverLetter(
        user_id=current_user.id,
        title=data.title,
        company_id=data.company_id,
        resume_profile_id=data.resume_profile_id,
    )
    db.add(cl)
    db.commit()
    db.refresh(cl)
    return cl


@router.get("/{cl_id}", response_model=CoverLetterWithItems)
def get_cover_letter(
    cl_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    return _get_cl_or_404(cl_id, current_user.id, db)


@router.put("/{cl_id}", response_model=CoverLetterOut)
def update_cover_letter(
    cl_id: int,
    data: CoverLetterUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    cl = _get_cl_or_404(cl_id, current_user.id, db)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(cl, field, value)
    db.commit()
    db.refresh(cl)
    return cl


@router.delete("/{cl_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_cover_letter(
    cl_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    cl = _get_cl_or_404(cl_id, current_user.id, db)
    db.delete(cl)
    db.commit()


# ─── Item CRUD ────────────────────────────────────────────────────────────────

@router.post("/{cl_id}/items", response_model=CoverLetterItemOut, status_code=status.HTTP_201_CREATED)
def add_item(
    cl_id: int,
    data: CoverLetterItemCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    _get_cl_or_404(cl_id, current_user.id, db)
    item = CoverLetterItem(cover_letter_id=cl_id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/items/{item_id}", response_model=CoverLetterItemOut)
def update_item(
    item_id: int,
    data: CoverLetterItemUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    item = db.query(CoverLetterItem).join(CoverLetter).filter(
        CoverLetterItem.id == item_id,
        CoverLetter.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    db.commit()
    db.refresh(item)
    return item


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    item = db.query(CoverLetterItem).join(CoverLetter).filter(
        CoverLetterItem.id == item_id,
        CoverLetter.user_id == current_user.id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
    db.delete(item)
    db.commit()


# ─── AI 초안 생성 ─────────────────────────────────────────────────────────────

@router.post("/{cl_id}/generate")
async def generate_drafts(
    cl_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """이력서 + 기업 분석 데이터 기반으로 자소서 각 문항 AI 초안 생성"""
    cl = _get_cl_or_404(cl_id, current_user.id, db)
    items = db.query(CoverLetterItem).filter(
        CoverLetterItem.cover_letter_id == cl_id
    ).order_by(CoverLetterItem.order_index).all()

    if not items:
        raise HTTPException(status_code=400, detail="문항이 없습니다. 먼저 자소서 문항을 추가해주세요.")

    # 이력서 데이터 수집
    resume_summary = ""
    if cl.resume_profile_id:
        profile = db.query(ResumeProfile).filter(ResumeProfile.id == cl.resume_profile_id).first()
        if profile:
            resume_items = db.query(ResumeItem).filter(ResumeItem.profile_id == profile.id).all()
            lines = []
            for it in resume_items:
                line = f"[{it.category.value}] {it.title}"
                if it.organization:
                    line += f" @ {it.organization}"
                lines.append(line)
                if it.description:
                    lines.append(f"  {it.description}")
            resume_summary = "\n".join(lines)

    # 기업 분석 데이터 수집
    job_summary = ""
    if cl.company_id:
        company = db.query(SavedCompany).filter(SavedCompany.id == cl.company_id).first()
        if company and company.analysis:
            a = company.analysis
            job_summary = (
                f"회사: {a.get('company_name', '')}\n"
                f"직무: {a.get('job_title', '')}\n"
                f"개요: {a.get('overview', '')}\n"
                f"기술스택: {', '.join(a.get('tech_stack', []))}\n"
                f"자격요건: {'; '.join(a.get('requirements', []))}"
            )

    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        import json
        import re

        def extract_json(raw: str) -> str:
            match = re.search(r'```(?:json)?\s*([\s\S]*?)```', raw)
            if match:
                return match.group(1).strip()
            return raw.strip()

        # 컨텍스트 크기 제한
        resume_ctx = resume_summary[:3000] if resume_summary else "(이력서 정보 없음)"
        job_ctx = job_summary[:2000] if job_summary else "(기업 정보 없음)"

        llm = ChatGoogleGenerativeAI(
            model=settings.AI_MODEL_NAME,
            google_api_key=settings.GOOGLE_API_KEY,
            request_timeout=settings.AI_LLM_TIMEOUT,
            temperature=0.4,
            max_output_tokens=2048,
            model_kwargs={"response_mime_type": "application/json"},
        )

        questions_block = "\n".join([
            f"{i+1}. {item.question}" + (f" (글자수 제한: {item.char_limit}자)" if item.char_limit else "")
            for i, item in enumerate(items)
        ])

        prompt = f"""당신은 취업 전문 컨설턴트입니다. 아래 지원자 정보와 기업 정보를 바탕으로 자소서 각 문항의 초안을 작성해주세요.

【지원자 이력서】
{resume_ctx}

【지원 기업 정보】
{job_ctx}

【자소서 문항 목록】
{questions_block}

각 문항에 대한 초안을 아래 JSON 배열 형식으로 반환해주세요 (JSON만 출력):
[
  {{"question_index": 1, "draft": "문항1 초안 내용"}},
  {{"question_index": 2, "draft": "문항2 초안 내용"}}
]

중요:
- 지원자의 실제 경험을 최대한 반영
- 구체적이고 진솔한 문체로 작성
- 글자수 제한이 있으면 반드시 준수"""

        response = await asyncio.to_thread(llm.invoke, prompt)
        text = extract_json(response.content.strip())

        drafts = json.loads(text)

        # DB 업데이트
        updated = []
        for d in drafts:
            idx = d.get("question_index", 0) - 1
            if 0 <= idx < len(items):
                items[idx].answer = d.get("draft", "")
                updated.append({"id": items[idx].id, "answer": items[idx].answer})

        db.commit()
        return {"updated": updated}

    except Exception as e:
        logger.error(f"AI 초안 생성 실패: {e}")
        raise HTTPException(status_code=500, detail=f"AI 초안 생성 중 오류가 발생했습니다: {str(e)}")
