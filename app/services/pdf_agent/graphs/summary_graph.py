from langgraph.graph import StateGraph
import nodes.summary as summary


def add_summary_node_on_graph(graph: StateGraph) -> StateGraph:
    graph.add_node("start_point_of_summary",summary.start_point_of_summary)
    graph.add_node("get_related_pdf",summary.get_related_pdf)
    graph.add_node("pdf_parsing",summary.pdf_parsing)
    graph.add_node("summary_pdf",summary.summary_pdf)
    graph.add_node("refine_textbook",summary.refine_textbook)
    graph.add_node("get_need_to_explain",summary.get_need_to_explain)
    graph.add_node("explain",summary.explain)
    graph.add_node("add_explanation",summary.add_explaination)
    graph.add_node("gen_question",summary.gen_sample_question)
    graph.add_node("save_file",summary.save_file)
    return graph

def add_summary_edge_on_graph(graph: StateGraph) -> StateGraph:
    graph.add_edge("start_point_of_summary","get_related_pdf")
    graph.add_edge("get_related_pdf","pdf_parsing")
    graph.add_edge("pdf_parsing","summary_pdf")
    graph.add_conditional_edges(
        "summary_pdf",
        summary.check_summary_completion,
        {
            "continue" : "summary_pdf",
            "completion": "refine_textbook"
        }
    )
    graph.add_edge("refine_textbook","get_need_to_explain")
    graph.add_edge("get_need_to_explain","explain")
    graph.add_conditional_edges(
        "explain",
        summary.check_explain_completion,
        {
            "continue" : "explain",
            "completion": "add_explanation"
        }
    )
    graph.add_edge("add_explanation","gen_question")
    graph.add_edge("gen_question","save_file")
    graph.add_edge("save_file","input_question")
    return graph

def get_summary_graph(graph: StateGraph) -> StateGraph:
    graph = add_summary_node_on_graph(graph)
    graph = add_summary_edge_on_graph(graph)

    return graph



# def add_node_on_summary_graph(graph:StateGraph)->StateGraph:
#     graph.add_node("pdf_parse",summary.pdf_parsing)
#     graph.add_node("summarize",summary.summary_pdf)
#     graph.add_node("refine_textbook",summary.refine_textbook)
#     graph.add_node("get_need_to_explain", summary.get_need_to_explain)
#     graph.add_node("explain",summary.explain)
#     graph.add_node("add_explanation",summary.add_explain)
#     graph.add_node("gen_question",summary.gen_sample_question)
#     graph.add_node("extract_pdf",summary.extract_pdf)

#     return graph

# def add_edge_on_summary_graph(graph:StateGraph) -> StateGraph:
#     graph.add_edge("router","pdf_parse")
#     graph.add_edge("pdf_parse","summarize")
#     graph.add_conditional_edges(
#         "summarize",
#         summary.check_summary_completion,
#         {
#             "continue" : "summarize",
#             "completion": "refine_textbook"
#         }
#     )
#     graph.add_edge("refine_textbook","get_need_to_explain")
#     graph.add_edge("get_need_to_explain","explain")
#     graph.add_conditional_edges(
#         "explain",
#         summary.check_explain_completion,
#         {
#             "continue" : "explain",
#             "completion": "add_explanation"
#         }
#     )
#     graph.add_edge("add_explanation","gen_question")
#     graph.add_edge("gen_question","extract_pdf")
#     graph.add_edge("extract_pdf","start")
#     return graph

# def get_summary_graph(graph : StateGraph):
#     graph = add_node_on_summary_graph(graph)
#     graph = add_edge_on_summary_graph(graph)

#     return graph


