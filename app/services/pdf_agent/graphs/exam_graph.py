from langgraph.graph import StateGraph
import nodes.exam as exam


def add_exam_node_on_graph(graph: StateGraph) -> StateGraph:
    graph.add_node("start_point_of_exam",exam.start_point_of_exam)
    return graph

def add_exam_edge_on_graph(graph: StateGraph) -> StateGraph:
    graph.add_edge("start_point_of_exam","input_question")
    return graph

def get_exam_graph(graph: StateGraph) -> StateGraph:
    graph = add_exam_node_on_graph(graph)
    graph = add_exam_edge_on_graph(graph)

    return graph