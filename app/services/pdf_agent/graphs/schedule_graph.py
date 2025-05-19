from langgraph.graph import StateGraph

from app.services.pdf_agent.nodes import scheduler


def add_schedule_node_on_graph(graph: StateGraph) -> StateGraph:
    graph.add_node("start_point_of_schedule",scheduler.start_point_of_schedule)
    graph.add_node("select_subjects",scheduler.select_subjects)
    graph.add_node("select_importance",scheduler.select_importance)
    graph.add_node("select_deadlines",scheduler.select_deadlines)
    graph.add_node("select_folder_for_schedule",scheduler.select_folder_for_schedule)
    graph.add_node("get_all_document",scheduler.get_all_document)
    graph.add_node("define_final_index",scheduler.define_final_index)
    graph.add_node("make_plans",scheduler.make_plans)
    graph.add_node("save_plan",scheduler.save_plan)
    return graph

def add_schedule_edge_on_graph(graph: StateGraph) -> StateGraph:
    graph.add_edge("start_point_of_schedule","select_subjects") 
    graph.add_edge("select_subjects","select_importance") 
    graph.add_edge("select_importance","select_deadlines") 
    graph.add_edge("select_deadlines","select_folder_for_schedule")
    graph.add_edge("select_folder_for_schedule","get_all_document")
    graph.add_edge("get_all_document","define_final_index")
    graph.add_conditional_edges(
        "define_final_index",
        scheduler.check_sub_count,
        {
            "completion" : "make_plans",
            "continue" : "select_folder_for_schedule"
        }
    )
    graph.add_edge("make_plans","save_plan")
    graph.add_edge("save_plan","input_question")

    return graph

def get_schedule_graph(graph: StateGraph) -> StateGraph:
    graph = add_schedule_node_on_graph(graph)
    graph = add_schedule_edge_on_graph(graph)
    
    return graph