# app/services/pdf_agent/states.py

from typing import TypedDict, List, Dict, Any, Optional


class AgentState(TypedDict, total=False):
    pdf_path: str
    pdfs: List[Any]  # PDF Document 목록
    pdf_step: int
    messages: List[Dict[str, Any]]  # LangChain Message 타입을 딕셔너리로 표현
    summaries: str
    result: str
    need_to_explain: Dict[str, Any]
    explain_step: int
    previous_exam_problems: List[Any]
    analysis_of_exam_writers: str
