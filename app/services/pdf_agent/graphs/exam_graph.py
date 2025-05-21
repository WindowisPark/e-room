from langgraph.graph import StateGraph
from app.services.pdf_agent.nodes import exam
from app.services.pdf_agent.states import AgentState


def add_exam_node_on_graph(graph: StateGraph) -> StateGraph:
    graph.add_node("start_point_of_exam", exam.start_point_of_exam)
    # input_question 노드 추가
    graph.add_node("input_question", lambda x: x)  # 단순 통과 함수
    return graph

def add_exam_edge_on_graph(graph: StateGraph) -> StateGraph:
    graph.add_edge("start_point_of_exam","input_question")
    return graph

def get_exam_graph():
    # StateGraph 초기화 추가
    graph = StateGraph(AgentState)
    graph = add_exam_node_on_graph(graph)
    graph = add_exam_edge_on_graph(graph)
    
    # 시작점 설정 추가
    graph.set_entry_point("start_point_of_exam")
    
    return graph.compile()