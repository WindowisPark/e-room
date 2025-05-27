from langgraph.graph import StateGraph
from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.nodes import exam


def add_exam_node_on_graph(graph: StateGraph) -> StateGraph:
   """시험 문제 생성 관련 노드들을 그래프에 추가"""
   # 시작점
   graph.add_node("start_point_of_exam", exam.start_point_of_exam)
   
   # 출제자 성향 분석 (기출문제 있을 때만)
   graph.add_node("select_previous_exam", exam.select_previous_exam)
   graph.add_node("analyze_previous_exam", exam.analyze_previous_exam)
   graph.add_node("get_final_personality", exam.get_final_personality)
   
   # 시험 문제 생성
   graph.add_node("select_exam_docs",exam.select_exam_docs)
   graph.add_node("get_all_files",exam.get_all_files)
   graph.add_node("get_concept_for_exam",exam.get_concept_for_exam)
   graph.add_node("refine_problems",exam.refine_problems)
   graph.add_node("save_exam",exam.save_exam)
   
   return graph


def add_exam_edge_on_graph(graph: StateGraph) -> StateGraph:
    graph.add_edge("start_point_of_exam","select_previous_exam")
    graph.add_conditional_edges(
        "select_previous_exam",
        exam.check_exist_previous_exam,
        {
            "no exist" : "select_exam_docs",
            "exist" : "analyze_previous_exam"
        }
    )
    graph.add_edge("analyze_previous_exam","get_final_personality")
    graph.add_edge("get_final_personality","select_exam_docs")
    graph.add_edge("select_exam_docs","get_all_files")
    graph.add_edge("get_all_files","get_concept_for_exam")
    graph.add_edge("get_concept_for_exam","refine_problems")
    graph.add_edge("refine_problems","save_exam")
    graph.add_edge("save_exam", "finish")  # input_question 대신 finish로
    return graph

def get_exam_graph(graph: StateGraph) -> StateGraph:
    graph = add_exam_node_on_graph(graph)
    graph = add_exam_edge_on_graph(graph)
    
    return graph


def build_exam_graph() -> StateGraph:
   """메인 그래프에서 호출할 수 있는 별칭 함수"""
   return get_exam_graph()