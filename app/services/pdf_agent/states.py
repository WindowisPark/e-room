from typing import TypedDict, List

class AgentState(TypedDict):
    pdf_path : str
    pdfs : List # pdf Document 담는 list
    pdf_step : int = 0
    messages : List[dict] # message들을 담는 list
    summaries : str # 요약한 내용을 담는 문자열
    result : str # 최종적으로 다듬은 내용을 담은 문자열
    need_to_explain : dict
    explain_step : int
    previous_exam_problems : List # 시험 기출 문제 Documents들을 담는 list
    analysis_of_exam_writers : str