# app/services/pdf_agent/states.py

from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict, total=False):
    pdf_path: str
    pdfs: List[Any]
    pdf_step: int
    messages: List[Dict[str, Any]]
    summaries: str
    result: str
    need_to_explain: Dict[str, Any]
    explain_step: int
    previous_exam_problems: List[Any]
    analysis_of_exam_writers: str

    # LangGraph 동작에 필요한 추가 필드들
    user_id: str
    folder: str
    document_id: int          # ✅ 추가!
    purpose: str
    full_document: bool
    pdf_content: str
    subject_index: int
    final_index: List[Any]
    personality: List[Any]
    final_personality: str
