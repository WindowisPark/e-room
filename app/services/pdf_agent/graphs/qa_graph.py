from langgraph.graph import StateGraph
from app.services.pdf_agent.nodes import qa_system
from app.services.pdf_agent.states import AgentState


def add_qa_node_on_graph(graph: StateGraph) -> StateGraph:
    graph.add_node("start_point_of_qa_system", qa_system.start_point_of_qa_system)
    # input_question 노드 추가
    graph.add_node("input_question", lambda x: x)  # 단순 통과 함수
    return graph

def add_qa_edge_on_graph(graph: StateGraph) -> StateGraph:
    graph.add_edge("start_point_of_qa_system","input_question")
    return graph

def get_qa_graph():
    # StateGraph 초기화 추가
    graph = StateGraph(AgentState)
    graph = add_qa_node_on_graph(graph)
    graph = add_qa_edge_on_graph(graph)
    
    # 시작점 설정 - 이 부분이 누락되었습니다
    graph.set_entry_point("start_point_of_qa_system")
    
    return graph.compile()