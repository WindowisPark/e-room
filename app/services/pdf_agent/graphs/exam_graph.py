from langgraph.graph import StateGraph
from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.nodes import exam


def add_exam_node_on_graph(graph: StateGraph) -> StateGraph:
    graph.add_node("start_point_of_exam",exam.start_point_of_exam)
    """출제자 성향 분석"""
    graph.add_node("select_previous_exam",exam.select_previous_exam)
    graph.add_node("analyze_previous_exam",exam.analyze_previous_exam)
    graph.add_node("get_final_personality",exam.get_final_personality)
    """시험 문제 생성"""
    graph.add_node("get_all_files",exam.get_all_files)
    graph.add_node("get_concept_for_exam",exam.get_concept_for_exam)
    graph.add_node("refine_problems",exam.refine_problems)

    return graph

def add_exam_edge_on_graph(graph: StateGraph) -> StateGraph:
    graph.add_edge("start_point_of_exam","select_previous_exam")
    graph.add_conditional_edges(
        "select_previous_exam",
        exam.check_exist_previous_exam,
        {
            "no exist": "input_question",  # 다시 질문 입력 상태로 회귀
            "exist": "analyze_previous_exam"
        }
    )
    graph.add_conditional_edges(
        "analyze_previous_exam",
        exam.check_exam_count,
        {
            "completion": "get_final_personality",
            "continue": "analyze_previous_exam"
        }
    )
    graph.add_edge("get_final_personality","get_all_files")
    graph.add_edge("get_all_files","get_concept_for_exam")
    graph.add_edge("get_concept_for_exam","refine_problems")
    return graph

def get_exam_graph(graph: StateGraph) -> StateGraph:
    graph = add_exam_node_on_graph(graph)
    graph = add_exam_edge_on_graph(graph)
    
    return graph