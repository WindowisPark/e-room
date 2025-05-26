# app/services/pdf_agent/graphs/qa_graph.py

from langgraph.graph import StateGraph
from app.services.pdf_agent.nodes import qa_system
from app.services.pdf_agent.states import AgentState


def add_qa_node_on_graph(graph: StateGraph) -> StateGraph:
    graph.add_node("start_point_of_qa_system", qa_system.start_point_of_qa_system)
    return graph


def add_qa_edge_on_graph(graph: StateGraph) -> StateGraph:
    graph.add_edge("start_point_of_qa_system","input_question")
    return graph


def get_qa_graph(graph: StateGraph) -> StateGraph:
    graph = add_qa_node_on_graph(graph)
    graph = add_qa_edge_on_graph(graph)
    
    return graph