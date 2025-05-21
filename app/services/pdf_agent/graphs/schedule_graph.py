# app/services/pdf_agent/graphs/schedule_graph.py

from langgraph.graph import StateGraph
from app.services.pdf_agent.nodes import scheduler
from app.services.pdf_agent.states import AgentState


def add_schedule_node_on_graph(graph: StateGraph) -> StateGraph:
    # 학습 스케줄 노드 등록
    graph.add_node("start_point_of_schedule", scheduler.start_point_of_schedule)
    graph.add_node("select_subjects", scheduler.select_subjects)
    graph.add_node("select_importance", scheduler.select_importance)
    graph.add_node("select_deadlines", scheduler.select_deadlines)
    graph.add_node("select_folder_for_schedule", scheduler.select_folder_for_schedule)
    graph.add_node("get_all_document", scheduler.get_all_document)
    graph.add_node("define_final_index", scheduler.define_final_index)
    graph.add_node("make_plans", scheduler.make_plans)
    graph.add_node("save_plan", scheduler.save_plan)
    graph.add_node("input_question", lambda x: x)  # 종료용 통과 노드
    return graph


def add_schedule_edge_on_graph(graph: StateGraph) -> StateGraph:
    # 흐름 정의
    graph.add_edge("start_point_of_schedule", "select_subjects")
    graph.add_edge("select_subjects", "select_importance")
    graph.add_edge("select_importance", "select_deadlines")
    graph.add_edge("select_deadlines", "select_folder_for_schedule")
    graph.add_edge("select_folder_for_schedule", "get_all_document")
    graph.add_edge("get_all_document", "define_final_index")
    graph.add_conditional_edges(
        "define_final_index",
        scheduler.check_sub_count,
        {
            "completion": "make_plans",
            "continue": "select_folder_for_schedule"
        }
    )
    graph.add_edge("make_plans", "save_plan")
    graph.add_edge("save_plan", "input_question")
    return graph


def get_schedule_graph() -> StateGraph:
    # 전체 스케줄 그래프 구성 및 컴파일
    graph = StateGraph(AgentState)
    graph = add_schedule_node_on_graph(graph)
    graph = add_schedule_edge_on_graph(graph)
    graph.set_entry_point("start_point_of_schedule")
    return graph.compile()
