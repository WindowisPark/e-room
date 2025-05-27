# app/services/pdf_agent/states.py (완전한 AgentState 정의)

from typing import TypedDict, List, Dict, Any, Optional
from langchain_core.messages import BaseMessage

class AgentState(TypedDict, total=False):
    """
    PDF Agent의 상태를 정의하는 TypedDict
    total=False로 설정하여 모든 키가 선택적이 되도록 함
    """
    
    # ==================== 기본 정보 ====================
    user_id: str
    document_id: int
    pdf_path: str
    purpose: str
    folder: str
    query: str
    
    # ==================== 메시지 관련 ====================
    messages: List[BaseMessage]
    last_user_query: str
    last_assistant_response: str
    
    # ==================== PDF 처리 관련 ====================
    pdf_text: str
    pdf_content: str
    structure: Dict[str, Any]
    doc_chunks: List[Dict[str, Any]]
    pdfs: List[str]  # 분할된 PDF 텍스트들
    
    # ==================== 요약 관련 ====================
    summaries: str
    result: str
    need_to_explain: Dict[str, Any]
    explain_step: int
    
    # ==================== 시험 문제 생성 관련 ====================
    exam_step: str
    previous_exam_path: List[str]
    exam_docs_path: str
    exam_docs: str
    personality: List[str]
    final_personality: str
    concepts_for_exam: List[str]
    problems: List[str]
    
    # ==================== 스케줄러 관련 ====================
    scheduler_step: str
    subjects: List[str]
    subject_index: int
    importance: Dict[str, int]
    deadlines: Dict[str, str]
    selected_files: List[str]
    docs: List[str]
    final_index: List[str]
    schedule: Dict[str, Any]
    schedule_file_path: str
    
    # ==================== 기타 상태 ====================
    embedding_stored: bool
    error: Optional[str]
    
    # ==================== WebSocket 관련 추가 상태 ====================
    waiting_for: Optional[str]  # "file_selection", "importance_input", "deadline_input" 등
    current_request_type: Optional[str]  # "summary_target", "previous_exam", "study_material" 등
    scheduler_data: Optional[Dict[str, Any]]  # 스케줄러 임시 데이터
    
    # ==================== 파일 경로 관련 ====================
    saved_path: Optional[str]  # 저장된 파일 경로
    file_path: Optional[str]   # 일반적인 파일 경로