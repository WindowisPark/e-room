from ..nodes import summary
from langgraph.graph import StateGraph

def add_node_on_summary_graph(graph: StateGraph) -> StateGraph:
    graph.add_node("pdf_parse", summary.pdf_parsing)
    graph.add_node("summarize", summary.summary_pdf)
    graph.add_node("refine_textbook", summary.refine_textbook)
    graph.add_node("get_need_to_explain", summary.get_need_to_explain)
    graph.add_node("explain", summary.explain)
    graph.add_node("add_explanation", summary.add_explain)
    graph.add_node("gen_question", summary.gen_sample_question)
    graph.add_node("extract_pdf", summary.extract_pdf)

    return graph

def add_edge_on_summary_graph(graph: StateGraph) -> StateGraph:
    graph.set_entry_point("pdf_parse")
    graph.add_edge("pdf_parse", "summarize")
    graph.add_conditional_edges(
        "summarize",
        summary.check_summary_completion,
        {
            "continue": "summarize",
            "completion": "refine_textbook"
        }
    )
    graph.add_edge("refine_textbook", "get_need_to_explain")
    graph.add_edge("get_need_to_explain", "explain")
    graph.add_conditional_edges(
        "explain",
        summary.check_explain_completion,
        {
            "continue": "explain",
            "completion": "add_explanation"
        }
    )
    graph.add_edge("add_explanation", "gen_question")
    graph.add_edge("gen_question", "extract_pdf")
    graph.set_finish_point("extract_pdf")
    return graph

def get_summary_graph(graph: StateGraph):
    graph = add_node_on_summary_graph(graph)
    graph = add_edge_on_summary_graph(graph)

    return graph