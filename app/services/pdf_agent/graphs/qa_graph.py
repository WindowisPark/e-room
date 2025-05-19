from langgraph.graph import StateGraph
import nodes.qa_system as qa_system


def add_qa_node_on_graph(graph: StateGraph) -> StateGraph:
    graph.add_node("start_point_of_qa_system",qa_system.start_point_of_qa_system)
    return graph

def add_qa_edge_on_graph(graph: StateGraph) -> StateGraph:
    graph.add_edge("start_point_of_qa_system","input_question")
    return graph

def get_qa_graph(graph: StateGraph) -> StateGraph:
    graph = add_qa_node_on_graph(graph)
    graph = add_qa_edge_on_graph(graph)

    return graph