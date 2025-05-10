from langgraph.graph import StateGraph
from ..states import AgentState
from ..nodes import summary as summary
from .summary_graph import get_summary_graph

def start_graph()->StateGraph:
    return StateGraph(AgentState)

def intergrate_graph() :
    graph = start_graph()
    graph = get_summary_graph(graph)
    chain = graph.compile()
    return chain