# app/api/v1/endpoints/resume.py

import json
from typing import List, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.api import deps
from app.db.session import get_db
from app.models.user import User
from app.models.resume import ResumeProfile, ResumeItem, ItemCategory

router = APIRouter()


# ─── Pydantic Schemas ────────────────────────────────────────────────────────

class ResumeProfileCreate(BaseModel):
    title: str
    summary: Optional[str] = None


class ResumeProfileUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None


class ResumeProfileOut(BaseModel):
    id: int
    user_id: int
    title: str
    summary: Optional[str]
    updated_at: Any
    created_at: Any

    class Config:
        from_attributes = True


class ResumeItemCreate(BaseModel):
    category: ItemCategory
    title: str
    organization: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    order_index: Optional[int] = 0


class ResumeItemUpdate(BaseModel):
    category: Optional[ItemCategory] = None
    title: Optional[str] = None
    organization: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    order_index: Optional[int] = None


class ResumeItemOut(BaseModel):
    id: int
    profile_id: int
    category: ItemCategory
    title: str
    organization: Optional[str]
    start_date: Optional[str]
    end_date: Optional[str]
    description: Optional[str]
    tags: Optional[List[str]]
    order_index: int

    class Config:
        from_attributes = True


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_profile_or_404(profile_id: int, user_id: int, db: Session) -> ResumeProfile:
    profile = db.query(ResumeProfile).filter(
        ResumeProfile.id == profile_id,
        ResumeProfile.user_id == user_id
    ).first()
    if not profile:
        raise HTTPException(status_code=404, detail="이력서를 찾을 수 없습니다.")
    return profile


def _get_item_or_404(item_id: int, user_id: int, db: Session) -> ResumeItem:
    item = db.query(ResumeItem).join(ResumeProfile).filter(
        ResumeItem.id == item_id,
        ResumeProfile.user_id == user_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="항목을 찾을 수 없습니다.")
    return item


# ─── Profile CRUD ─────────────────────────────────────────────────────────────

@router.get("/profiles", response_model=List[ResumeProfileOut])
def list_profiles(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    return db.query(ResumeProfile).filter(ResumeProfile.user_id == current_user.id).order_by(ResumeProfile.created_at.desc()).all()


@router.post("/profiles", response_model=ResumeProfileOut, status_code=status.HTTP_201_CREATED)
def create_profile(
    data: ResumeProfileCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    profile = ResumeProfile(user_id=current_user.id, title=data.title, summary=data.summary)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/profiles/{profile_id}", response_model=ResumeProfileOut)
def get_profile(
    profile_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    return _get_profile_or_404(profile_id, current_user.id, db)


@router.put("/profiles/{profile_id}", response_model=ResumeProfileOut)
def update_profile(
    profile_id: int,
    data: ResumeProfileUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    profile = _get_profile_or_404(profile_id, current_user.id, db)
    if data.title is not None:
        profile.title = data.title
    if data.summary is not None:
        profile.summary = data.summary
    db.commit()
    db.refresh(profile)
    return profile


@router.delete("/profiles/{profile_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_profile(
    profile_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    profile = _get_profile_or_404(profile_id, current_user.id, db)
    db.delete(profile)
    db.commit()


# ─── Item CRUD ────────────────────────────────────────────────────────────────

@router.get("/profiles/{profile_id}/items", response_model=List[ResumeItemOut])
def list_items(
    profile_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    _get_profile_or_404(profile_id, current_user.id, db)
    return db.query(ResumeItem).filter(ResumeItem.profile_id == profile_id).order_by(ResumeItem.order_index).all()


@router.post("/profiles/{profile_id}/items", response_model=ResumeItemOut, status_code=status.HTTP_201_CREATED)
def add_item(
    profile_id: int,
    data: ResumeItemCreate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    _get_profile_or_404(profile_id, current_user.id, db)
    item = ResumeItem(profile_id=profile_id, **data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.put("/items/{item_id}", response_model=ResumeItemOut)
def update_item(
    item_id: int,
    data: ResumeItemUpdate,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    item = _get_item_or_404(item_id, current_user.id, db)
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
    item = _get_item_or_404(item_id, current_user.id, db)
    db.delete(item)
    db.commit()


# ─── Export ──────────────────────────────────────────────────────────────────

@router.get("/profiles/{profile_id}/export/json")
def export_json(
    profile_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """JSON Resume 표준 포맷(https://jsonresume.org/schema/) 으로 내보내기"""
    profile = _get_profile_or_404(profile_id, current_user.id, db)
    items = db.query(ResumeItem).filter(ResumeItem.profile_id == profile_id).order_by(ResumeItem.order_index).all()

    def _period(item):
        return {
            "startDate": item.start_date or "",
            "endDate": item.end_date or ""
        }

    json_resume: Dict[str, Any] = {
        "basics": {
            "name": current_user.full_name or current_user.username,
            "email": current_user.email or "",
            "summary": profile.summary or ""
        },
        "work": [],
        "education": [],
        "skills": [],
        "certificates": [],
        "volunteer": [],
        "projects": [],
    }

    for item in items:
        if item.category == ItemCategory.experience:
            json_resume["work"].append({
                "name": item.organization or "",
                "position": item.title,
                "summary": item.description or "",
                **_period(item),
                "keywords": item.tags or []
            })
        elif item.category == ItemCategory.education:
            json_resume["education"].append({
                "institution": item.organization or "",
                "area": item.title,
                "summary": item.description or "",
                **_period(item)
            })
        elif item.category == ItemCategory.skill:
            json_resume["skills"].append({
                "name": item.title,
                "keywords": item.tags or []
            })
        elif item.category == ItemCategory.cert:
            json_resume["certificates"].append({
                "name": item.title,
                "issuer": item.organization or "",
                "date": item.start_date or "",
                "summary": item.description or ""
            })
        elif item.category == ItemCategory.activity:
            json_resume["volunteer"].append({
                "organization": item.organization or "",
                "position": item.title,
                "summary": item.description or "",
                **_period(item)
            })
        elif item.category == ItemCategory.project:
            json_resume["projects"].append({
                "name": item.title,
                "description": item.description or "",
                "keywords": item.tags or [],
                **_period(item)
            })

    return JSONResponse(
        content=json_resume,
        headers={"Content-Disposition": f'attachment; filename="resume_{profile_id}.json"'}
    )


@router.get("/profiles/{profile_id}/export/pdf")
def export_pdf(
    profile_id: int,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user)
):
    """이력서 PDF 다운로드 (HTML → WeasyPrint)"""
    try:
        from weasyprint import HTML
    except ImportError:
        raise HTTPException(status_code=501, detail="PDF 생성 라이브러리(WeasyPrint)가 설치되지 않았습니다.")

    profile = _get_profile_or_404(profile_id, current_user.id, db)
    items = db.query(ResumeItem).filter(ResumeItem.profile_id == profile_id).order_by(ResumeItem.order_index).all()

    category_labels = {
        "experience": "경력",
        "project": "프로젝트",
        "cert": "자격증",
        "activity": "활동",
        "skill": "기술",
        "education": "학력",
    }

    sections: Dict[str, list] = {}
    for item in items:
        key = item.category.value
        sections.setdefault(key, []).append(item)

    rows_html = ""
    for cat, cat_items in sections.items():
        rows_html += f"<h2>{category_labels.get(cat, cat)}</h2><ul>"
        for it in cat_items:
            period = ""
            if it.start_date:
                period = f"{it.start_date} ~ {it.end_date or '현재'}"
            tags_str = ", ".join(it.tags) if it.tags else ""
            rows_html += (
                f"<li><strong>{it.title}</strong>"
                f"{' | ' + it.organization if it.organization else ''}"
                f"{' | ' + period if period else ''}"
                f"{'<br>' + it.description if it.description else ''}"
                f"{'<br><em>' + tags_str + '</em>' if tags_str else ''}"
                f"</li>"
            )
        rows_html += "</ul>"

    html_content = f"""
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<style>
  body {{ font-family: 'Noto Sans KR', sans-serif; margin: 40px; color: #333; }}
  h1 {{ font-size: 24px; border-bottom: 2px solid #F76707; padding-bottom: 8px; }}
  h2 {{ font-size: 16px; color: #F76707; margin-top: 20px; }}
  ul {{ list-style: none; padding: 0; }}
  li {{ margin-bottom: 10px; line-height: 1.6; }}
  em {{ color: #666; font-size: 12px; }}
</style>
</head>
<body>
  <h1>{profile.title}</h1>
  <p>{profile.summary or ''}</p>
  {rows_html}
</body>
</html>
"""

    pdf_bytes = HTML(string=html_content).write_pdf()

    return StreamingResponse(
        iter([pdf_bytes]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="resume_{profile_id}.pdf"'}
    )
