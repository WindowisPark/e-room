# app/services/pdf_agent/graphs/exam_graph.py

from langgraph.graph import StateGraph
from app.services.pdf_agent.nodes import exam
from app.services.pdf_agent.states import AgentState


def add_exam_node_on_graph(graph: StateGraph) -> StateGraph:
    graph.add_node("start_point_of_exam", exam.start_point_of_exam)
    graph.add_node("analyze_previous_exam", exam.analyze_previous_exam)
    graph.add_node("check_exam_count", exam.check_exam_count)
    graph.add_node("final_personality", exam.final_personality)
    graph.add_node("get_concept_for_exam", exam.get_concept_for_exam)
    graph.add_node("refine_problems", exam.refine_problems)
    return graph


def add_exam_edge_on_graph(graph: StateGraph) -> StateGraph:
    graph.add_edge("start_point_of_exam", "analyze_previous_exam")
    graph.add_conditional_edges(
        "analyze_previous_exam",
        exam.check_exam_count,
        {
            "continue": "analyze_previous_exam",
            "completion": "final_personality"
        }
    )
    graph.add_edge("final_personality", "get_concept_for_exam")
    graph.add_edge("get_concept_for_exam", "refine_problems")
    return graph


def get_exam_graph():
    graph = StateGraph(AgentState)
    graph = add_exam_node_on_graph(graph)
    graph = add_exam_edge_on_graph(graph)
    graph.set_entry_point("start_point_of_exam")
    return graph.compile()
