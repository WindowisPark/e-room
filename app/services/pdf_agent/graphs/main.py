from langgraph.graph import StateGraph
from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.nodes import summary
from app.services.pdf_agent.graphs.summary_graph import add_summary_edge_on_graph, add_summary_node_on_graph
from app.services.pdf_agent.graphs.schedule_graph import add_schedule_edge_on_graph, add_schedule_node_on_graph
from app.services.pdf_agent.graphs.qa_graph import add_qa_edge_on_graph, add_qa_node_on_graph
from app.services.pdf_agent.graphs.exam_graph import add_exam_edge_on_graph, add_exam_node_on_graph
from app.services.pdf_agent.graphs.common import add_common_edge_on_graph, add_common_node_on_graph

from app.services.pdf_agent.nodes.processor import (
    load_pdf_text,
    split_into_chunks,
    store_embedding
)

def start_graph()->StateGraph:
    return StateGraph(AgentState)

def intergrate_graph():
    graph = StateGraph(AgentState)

    # ✅ 새 노드 등록
    graph.add_node("load_pdf", load_pdf_text)
    graph.add_node("split_into_chunks", split_into_chunks)
    graph.add_node("store_embedding", store_embedding)

    # ✅ 기존 목적 라우팅 및 노드들
    graph = add_common_node_on_graph(graph)
    graph = add_summary_node_on_graph(graph)
    graph = add_exam_node_on_graph(graph)
    graph = add_qa_node_on_graph(graph)
    graph = add_schedule_node_on_graph(graph)

    # ✅ 흐름 연결
    graph.set_entry_point("load_pdf")
    graph.add_edge("load_pdf", "split_into_chunks")
    graph.add_edge("split_into_chunks", "store_embedding")
    graph.add_edge("store_embedding", "judge_the_purpose_of_the_input")

    # ✅ 목적별 흐름 추가 연결
    graph = add_common_edge_on_graph(graph)
    graph = add_summary_edge_on_graph(graph)
    graph = add_exam_edge_on_graph(graph)
    graph = add_qa_edge_on_graph(graph)
    graph = add_schedule_edge_on_graph(graph)

    return graph.compile()
