# app/services/pdf_agent/states.py
from typing import TypedDict, List, Dict, Any, Optional, Annotated, Callable
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage

# 리듀서 함수 정의
def message_reducer(a: List[BaseMessage], b: List[BaseMessage]) -> List[BaseMessage]:
    return b

def string_reducer(a: str, b: str) -> str:
    return b

def dict_reducer(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    return b

def int_reducer(a: int, b: int) -> int:
    return b

class MessageAnnotation:
    """메시지 상태 어노테이션"""
    @staticmethod
    def reduce(a: Any, b: Any) -> Any:
        return b if b is not None else a

class DocumentAnnotation:
    """문서 관련 상태 어노테이션"""
    @staticmethod
    def reduce(a: Any, b: Any) -> Any:
        return b if b is not None else a

class ProcessingAnnotation:
    """처리 관련 상태 어노테이션"""
    @staticmethod
    def reduce(a: Any, b: Any) -> Any:
        return b if b is not None else a

class AgentState(TypedDict, total=False):
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
    
    # 메시지 관련 상태
    messages: List[BaseMessage]
    last_user_query: str
    last_assistant_response: str
    
    # 문서 관련 상태
    pdf_text: str
    structure: Dict[str, Any]
    doc_chunks: List[Dict[str, Any]]
    
    # 처리 관련 상태
    summaries: str
    result: str
    need_to_explain: Dict[str, Any]
    explain_step: int