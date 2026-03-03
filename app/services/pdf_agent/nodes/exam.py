# app/services/pdf_agent/nodes/exam.py

from langchain_core.messages import AIMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.tools import get_all_docs
from app.services.pdf_agent.prompts.exam import (
    ANALYZE_EXAM_PROMPT,
    FINAL_PERSONALITY_PROMPT,
    CONCEPT_FOR_EXAM_PROMPT,
    REFINE_PROBLEMS_PROMPT,
)
from app.core.config import settings
from langchain_community.document_loaders import PDFPlumberLoader
from datetime import datetime
import os
import mimetypes
import base64
import logging

logger = logging.getLogger(__name__)
llm = ChatGoogleGenerativeAI(
    model=settings.AI_MODEL_NAME,
    google_api_key=settings.GOOGLE_API_KEY,
    request_timeout=settings.AI_LLM_TIMEOUT,
)

def start_point_of_exam(state: AgentState):
    logger.info("시험 그래프 시작")

def select_previous_exam(state : AgentState):
    previous_exam_path = state.get("previous_exam_path", [])
    return {"previous_exam_path": previous_exam_path}

def check_exist_previous_exam(state: AgentState):
    if len(state["previous_exam_path"])==0:
        return "no exist"
    else :
        return "exist"

def analyze_previous_exam(state:AgentState): # 과거 시험 문제 병합 및 파일 
    previous_exam = state["previous_exam_path"]
    personality = []
    for now_exam_file_path in previous_exam :
        loader = PDFPlumberLoader(now_exam_file_path) 
        docs = loader.load()
        full_text = ""
        for doc in docs :
            full_text += doc.page_content
        result = llm.invoke(ANALYZE_EXAM_PROMPT.format(full_text=full_text)).content
        personality.append(result)
        logger.info(f"출제자 성향 분석 완료: {len(personality)}번째")
    
    return {"personality":personality}

def get_final_personality(state: AgentState):
    personality = state["personality"]
    result = llm.invoke(FINAL_PERSONALITY_PROMPT.format(personality=personality)).content
    return {"final_personality" : result}

def select_exam_docs(state: AgentState):
    return {"exam_docs_path": state["pdf_path"]}

def get_all_files(state: AgentState):
    exam_docs = get_all_docs(state["exam_docs_path"])
    return {"exam_docs" : exam_docs}

def get_concept_for_exam(state: AgentState):
    ## LLM Query해서 요약본 파일 GET한게 result라 가정
    exam_docs = state["exam_docs"]
    personality = state["final_personality"]

    text_splitter = RecursiveCharacterTextSplitter( 
        chunk_size=4000,
        chunk_overlap=1000,
        length_function=len,
        is_separator_regex=False,
    )
    pdfs = text_splitter.create_documents([exam_docs]) # 분할
    prompts = [CONCEPT_FOR_EXAM_PROMPT.format(personality=personality, page_content=pdf.page_content) for pdf in pdfs]
    results = llm.batch(prompts)
    concepts_for_exam = [r.content for r in results]
    return {"concepts_for_exam":concepts_for_exam}

def refine_problems(state: AgentState):
    concepts_for_exam = state["concepts_for_exam"]
    personality = state["personality"]
    prompts = [REFINE_PROBLEMS_PROMPT.format(personality=personality, concept=concept) for concept in concepts_for_exam]
    results = llm.batch(prompts)
    problems = [r.content for r in results]
    return {"problems":problems}

def save_exam(state: AgentState):
    title = os.path.basename(state["exam_docs_path"])
    user_id = state["user_id"]
    user_dir = f"{user_id}/exam/"
    problems= "\n".join(state["problems"])

    os.makedirs(user_dir, exist_ok=True)
    with open(os.path.join(user_dir,f"{title}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md"), "w", encoding="utf-8") as md_file:
        md_file.write(problems)

    messages = state["messages"]
    messages.append(AIMessage(content=problems))
    
    return {"messages":messages}