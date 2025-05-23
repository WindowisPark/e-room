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
   graph.add_node("get_all_files", exam.get_all_files)
   graph.add_node("get_concept_for_exam", exam.get_concept_for_exam)
   graph.add_node("refine_problems", exam.refine_problems)
   
   # 기출문제 없을 때를 위한 간단한 문제 생성 노드
   graph.add_node("simple_problem_generation", exam.simple_problem_generation)
   
   return graph


def add_exam_edge_on_graph(graph: StateGraph) -> StateGraph:
   """시험 문제 생성 관련 엣지들을 그래프에 추가"""
   # 시작 → 기출문제 체크
   graph.add_edge("start_point_of_exam", "select_previous_exam")
   
   # 기출문제 존재 여부에 따른 분기
   graph.add_conditional_edges(
       "select_previous_exam",
       exam.check_exist_previous_exam,
       {
           "no_exist": "simple_problem_generation",  # 기출문제 없음 → 간단 생성
           "exist": "analyze_previous_exam"          # 기출문제 있음 → 성향 분석
       }
   )
   
   # 기출문제 분석 루프
   graph.add_conditional_edges(
       "analyze_previous_exam",
       exam.check_exam_count,
       {
           "completion": "get_final_personality",    # 분석 완료 → 성향 정리
           "continue": "analyze_previous_exam"       # 계속 분석
       }
   )
   
   # 성향 분석 완료 → 학습 파일 준비 → 개념 추출 → 문제 생성
   graph.add_edge("get_final_personality", "get_all_files")
   graph.add_edge("get_all_files", "get_concept_for_exam")
   graph.add_edge("get_concept_for_exam", "refine_problems")
   
   # 간단한 문제 생성은 바로 종료
   # simple_problem_generation은 자체적으로 result를 설정하고 종료
   
   return graph


def get_exam_graph() -> StateGraph:
   """시험 문제 생성 그래프 생성 및 컴파일"""
   graph = StateGraph(AgentState)
   graph = add_exam_node_on_graph(graph)
   graph = add_exam_edge_on_graph(graph)
   
   # 진입점 설정
   graph.set_entry_point("start_point_of_exam")
   
   return graph.compile()


def build_exam_graph() -> StateGraph:
   """메인 그래프에서 호출할 수 있는 별칭 함수"""
   return get_exam_graph()