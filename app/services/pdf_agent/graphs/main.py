# app/services/pdf_agent/graphs/main.py

from langgraph.graph import StateGraph
from app.services.pdf_agent.states import (
    AgentState, 
    MessageAnnotation, 
    DocumentAnnotation,
    ProcessingAnnotation
)
from app.services.pdf_agent.graphs.summary_graph import get_summary_graph
from app.services.pdf_agent.graphs.schedule_graph import add_schedule_edge_on_graph, add_schedule_node_on_graph
from app.services.pdf_agent.graphs.qa_graph import get_qa_graph
from app.services.pdf_agent.graphs.exam_graph import get_exam_graph
from app.services.pdf_agent.nodes.processor import load_pdf_text, split_into_chunks, store_embedding
from app.services.pdf_agent.nodes.common import (
    input_question, 
    judge_the_purpose_of_the_input, 
    select_folder, 
    router,
    process_user_input
)
import logging

logger = logging.getLogger(__name__)

def simple_graph():
    """
    단순화된 PDF 처리 그래프 - 충돌 문제 해결
    """
    try:
        # 그래프 초기화
        graph = StateGraph(AgentState)
        
        # 노드 추가
        graph.add_node("load_pdf", load_pdf_text)
        graph.add_node("split_chunks", split_into_chunks)
        graph.add_node("store_embeddings", store_embedding)
        graph.add_node("process_input", process_user_input)
        
        # 흐름 연결 - 선형적 순서로 실행
        graph.set_entry_point("load_pdf")
        graph.add_edge("load_pdf", "split_chunks")
        graph.add_edge("split_chunks", "store_embeddings")
        graph.add_edge("store_embeddings", "process_input")
        
        # 그래프 컴파일
        return graph.compile()
    
    except Exception as e:
        logger.error(f"간단한 그래프 구성 중 오류 발생: {str(e)}")
        raise

def intergrate_graph():
    """전체 LangGraph 흐름 통합 및 컴파일"""
    try:
        # 그래프 초기화
        graph = StateGraph(AgentState)
        
        # PDF 처리 노드 등록
        graph.add_node("load_pdf", load_pdf_text)
        graph.add_node("split_chunks", split_into_chunks)
        graph.add_node("store_embeddings", store_embedding)
        
        # 입력 처리 및 라우팅 노드
        graph.add_node("get_input", input_question)
        graph.add_node("select_folder", select_folder)
        graph.add_node("determine_purpose", judge_the_purpose_of_the_input)
        
        # 서브그래프 엔트리 포인트 노드
        graph.add_node("start_summary", lambda x: x)
        graph.add_node("start_qa", lambda x: x)
        graph.add_node("start_exam", lambda x: x)
        graph.add_node("start_schedule", lambda x: x)
        
        # 메인 그래프 경로 설정
        graph.set_entry_point("load_pdf")
        graph.add_edge("load_pdf", "split_chunks")
        graph.add_edge("split_chunks", "store_embeddings")
        graph.add_edge("store_embeddings", "get_input")
        graph.add_edge("get_input", "select_folder")
        graph.add_edge("select_folder", "determine_purpose")
        
        # 목적에 따른 라우팅
        graph.add_conditional_edges(
            "determine_purpose",
            router,
            {
                "summary": "start_summary",
                "qa_system": "start_qa",
                "generate_exam": "start_exam",
                "schedule": "start_schedule"
            }
        )
        
        # 그래프 컴파일
        return graph.compile()
    
    except Exception as e:
        logger.error(f"그래프 구성 중 오류 발생: {str(e)}")
        raise

def get_processing_graph():
    """
    문서 처리만 수행하는 단순 그래프
    """
    try:
        # 간소화된 방식 - dict 타입 사용
        graph = StateGraph(dict)
        
        # 디버깅을 위한 로깅 노드 추가
        def log_state(state):
            logger.info(f"그래프 처리 시작: 상태 내용 = {state}")
            return state
        
        graph.add_node("log_state", log_state)
        
        # 처리 노드 추가
        graph.add_node("load_pdf", load_pdf_text)
        graph.add_node("split_chunks", split_into_chunks)
        graph.add_node("store_embeddings", store_embedding)
        
        # 직렬화된 흐름 - 로깅 노드를 첫 번째로 추가
        graph.set_entry_point("log_state")
        graph.add_edge("log_state", "load_pdf")
        graph.add_edge("load_pdf", "split_chunks")
        graph.add_edge("split_chunks", "store_embeddings")
        
        return graph.compile()
    except Exception as e:
        logger.error(f"처리 그래프 생성 중 오류: {str(e)}", exc_info=True)
        # 기본 오류 처리 함수를 포함한 최소 그래프 반환
        graph = StateGraph(dict)
        graph.add_node("error", lambda state: {**state, "error": f"그래프 초기화 실패: {str(e)}"})
        graph.set_entry_point("error")
        return graph.compile()