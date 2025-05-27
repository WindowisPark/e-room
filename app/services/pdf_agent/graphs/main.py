from langgraph.graph import StateGraph
from app.services.pdf_agent.states import AgentState
import app.services.pdf_agent.nodes.summary as summary
from app.services.pdf_agent.graphs.summary_graph import add_summary_edge_on_graph,add_summary_node_on_graph
from app.services.pdf_agent.graphs.schedule_graph import add_schedule_edge_on_graph,add_schedule_node_on_graph
from app.services.pdf_agent.graphs.qa_graph import add_qa_edge_on_graph,add_qa_node_on_graph
from app.services.pdf_agent.graphs.exam_graph import add_exam_edge_on_graph,add_exam_node_on_graph
from app.services.pdf_agent.graphs.common import add_common_edge_on_graph,add_common_node_on_graph


def start_graph()->StateGraph:
    return StateGraph(AgentState)

def intergrate_graph() :
    graph = start_graph()
    graph = add_common_node_on_graph(graph)
    graph = add_summary_node_on_graph(graph)
    graph = add_exam_node_on_graph(graph)
    graph = add_qa_node_on_graph(graph)
    graph = add_schedule_node_on_graph(graph)
    graph = add_common_edge_on_graph(graph)
    graph = add_summary_edge_on_graph(graph)
    graph = add_exam_edge_on_graph(graph)
    graph = add_qa_edge_on_graph(graph)
    graph = add_schedule_edge_on_graph(graph)
    chain = graph.compile()

    
    
    return chain