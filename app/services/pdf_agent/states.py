# app/services/pdf_agent/states.py

from typing import TypedDict, List, Dict, Any, Optional, Annotated
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

# 상태 어노테이션을 위한 클래스
class MessageAnnotation:
    """메시지 상태 어노테이션"""
    pass

class DocumentAnnotation:
    """문서 관련 상태 어노테이션"""
    pass

class ProcessingAnnotation:
    """처리 관련 상태 어노테이션"""
    pass

class AgentState(TypedDict, total=False):
    # 메시지 관련 상태 (Annotated)
    messages: Annotated[List[BaseMessage], MessageAnnotation]
    last_user_query: Annotated[str, MessageAnnotation]
    last_assistant_response: Annotated[str, MessageAnnotation]
    
    # 문서 관련 상태 (Annotated)
    pdf_text: Annotated[str, DocumentAnnotation]
    structure: Annotated[Dict[str, Any], DocumentAnnotation]
    doc_chunks: Annotated[List[Dict[str, Any]], DocumentAnnotation]
    
    # 처리 관련 상태 (Annotated)
    summaries: Annotated[str, ProcessingAnnotation]
    result: Annotated[str, ProcessingAnnotation]
    need_to_explain: Annotated[Dict[str, Any], ProcessingAnnotation]
    explain_step: Annotated[int, ProcessingAnnotation]
    
    # 일반 상태 (비주석)
    user_id: str
    folder: str
    document_id: int
    purpose: str
    full_document: bool
    pdf_content: Optional[str]
    subject_index: int
    final_index: List[Any]
    personality: List[Any]
    final_personality: str
    pdf_path: Optional[str]
    pdf_step: int
    embedding_stored: bool
    error: Optional[str]