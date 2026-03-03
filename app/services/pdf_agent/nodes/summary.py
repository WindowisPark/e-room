# app/services/pdf_agent/nodes/summary.py

from app.services.pdf_agent.states import AgentState
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from app.services.pdf_agent.tools import get_all_docs
from app.services.pdf_agent.prompts.summary import (
    SUMMARY_PROMPT,
    EXTRACT_TERMS_PROMPT,
    EXPLAIN_TERM_PROMPT,
    ADD_EXPLANATION_PROMPT,
    SAMPLE_QUESTION_PROMPT,
)
from app.core.config import settings
import json
import os
import logging
from datetime import datetime

llm = ChatGoogleGenerativeAI(
    model=settings.AI_MODEL_NAME,
    google_api_key=settings.GOOGLE_API_KEY,
    request_timeout=settings.AI_LLM_TIMEOUT,
)
logger = logging.getLogger(__name__)

def start_point_of_summary(state: AgentState):
    return {"pdf_path": state["pdf_path"]}

def get_related_pdf(state: AgentState):
    pdf_path = state["pdf_path"]
    pdf = get_all_docs(pdf_path)
    return {"pdf_content": pdf}

def pdf_parsing(state: AgentState):
    pdf_content = state["pdf_content"]
    if len(pdf_content)>=15000 :
        text_splitter = RecursiveCharacterTextSplitter( # 3000자 단위로 split
            chunk_size=3000,
            chunk_overlap=100,
            length_function=len,
            is_separator_regex=False,
        )
    else : 
        chunk_size = len(pdf_content)/5
        text_splitter = RecursiveCharacterTextSplitter( # 3000자 단위로 split
            chunk_size=int(chunk_size),
            chunk_overlap=100,
            length_function=len,
            is_separator_regex=False,
        )
    pdfs = text_splitter.split_text(pdf_content)
    return {"pdfs":pdfs}

def summary_pdf(state:AgentState):
    pdfs = state["pdfs"]
    prompts = [SUMMARY_PROMPT.format(pdf=pdf) for pdf in pdfs]
    results = llm.batch(prompts)
    summaries = "".join(r.content for r in results)
    return {"result":summaries}


# 배경지식 설명 필요한거 찾기
def get_need_to_explain(state : AgentState) :
    result = state["result"]
    need_to_explain = llm.invoke(EXTRACT_TERMS_PROMPT.format(result=result))
    return { "need_to_explain" :json.loads(need_to_explain.content)}

def explain(state: AgentState):
    need_to_explain = state["need_to_explain"]
    keys = list(need_to_explain.keys())
    prompts = [EXPLAIN_TERM_PROMPT.format(value=need_to_explain[k], key=k) for k in keys]
    results = llm.batch(prompts)
    result_map = {k: r.content for k, r in zip(keys, results)}
    return {"need_to_explain" : result_map}
    
# 설명 본문에 추가
def add_explaination(state : AgentState):
    result = state["result"]
    need_to_explain = state["need_to_explain"]
    if len(result) < 20000 :
        chunk_size = len(result)/5
        text_splitter = RecursiveCharacterTextSplitter( # 3000자 단위로 split
                chunk_size=int(chunk_size),
                chunk_overlap=0,
                length_function=len,
                is_separator_regex=False,
        )
    else :
        text_splitter = RecursiveCharacterTextSplitter( # 3000자 단위로 split
                chunk_size=4000,
                chunk_overlap=0,
                length_function=len,
                is_separator_regex=False,
        )
    divided_results = text_splitter.split_text(result)
    prompts = [ADD_EXPLANATION_PROMPT.format(divided_result=dr, need_to_explain=need_to_explain) for dr in divided_results]
    batch_results = llm.batch(prompts)
    final_result = "".join(r.content for r in batch_results)
    
    user_id = state["user_id"]
    title = os.path.basename(state["pdf_path"])
    user_dir = f"{user_id}/summary" 
    os.makedirs(user_dir, exist_ok=True)
    with open(os.path.join(user_dir,f"{title}_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"), "w", encoding="utf-8") as md_file:
        md_file.write(result)

    return {"result": final_result}

# 학습 테스트용 문제 생성
def gen_sample_question(state:AgentState):
    result = state["result"]
    exam = llm.invoke(SAMPLE_QUESTION_PROMPT.format(result=result))
    return {"result":result+exam.content}

def save_file(state:AgentState):
    result = state["result"]
    user_id = state["user_id"]
    title = os.path.basename(state["pdf_path"])
    user_dir = f"{user_id}/summary" 
    os.makedirs(user_dir, exist_ok=True)
    with open(os.path.join(user_dir,f"{title}_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"), "w", encoding="utf-8") as md_file:
        md_file.write(result)
