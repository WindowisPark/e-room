from app.services.pdf_agent.nodes import common
from app.services.pdf_agent.nodes import exam
from app.services.pdf_agent.nodes import qa_system
from app.services.pdf_agent.nodes import scheduler
from app.services.pdf_agent.nodes import summary
from langgraph.graph import StateGraph

def add_common_node_on_graph(graph: StateGraph) -> StateGraph:
    graph.add_node("input_question",common.input_question)
    graph.add_node("judge_the_purpose_of_the_input",common.judge_the_purpose_of_the_input)
    graph.add_node("select_folder",common.select_folder)
    return graph

def add_common_edge_on_graph(graph: StateGraph) -> StateGraph:
    graph.set_entry_point("input_question")
    graph.add_edge("input_question","select_folder")
    graph.add_edge("select_folder","judge_the_purpose_of_the_input")
    graph.add_conditional_edges(
        "judge_the_purpose_of_the_input",
        common.router,
        {
            "summary" : "start_point_of_summary",
            "qa_system" : "start_point_of_qa_system",
            "generate_exam" : "start_point_of_exam",
            "schedule" : "start_point_of_schedule"
        }
    )


    return graph

def get_common_graph(graph : StateGraph):
    graph = add_common_node_on_graph(graph)
    graph = add_common_edge_on_graph(graph)

    return graph