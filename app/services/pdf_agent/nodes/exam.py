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

llm = ChatGoogleGenerativeAI(
    model=settings.AI_MODEL_NAME, google_api_key=settings.GOOGLE_API_KEY
)

def start_point_of_exam(state: AgentState):
    print("시험 그래프 시작")

def select_previous_exam(state : AgentState):
    previous_exam_path = input("기출 문제 경로를 입력해주세요.(띄어쓰기로 구분)").split() # 파일 경로임
    return {"previous_exam_path":previous_exam_path}

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
        print("=====출제자의 성향=====")
        print(personality)
    
    return {"personality":personality}

def get_final_personality(state: AgentState):
    personality = state["personality"]
    result = llm.invoke(FINAL_PERSONALITY_PROMPT.format(personality=personality)).content
    return {"final_personality" : result}

def select_exam_docs(state: AgentState):
    exam_docs_path = input("시험 문제 출제를 원하는 자료를 선택해주세요.(경로입력)")
    return {"exam_docs_path":exam_docs_path}

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
    concepts_for_exam = []
    for pdf in pdfs:
        concepts_for_exam.append(llm.invoke(CONCEPT_FOR_EXAM_PROMPT.format(personality=personality, page_content=pdf.page_content)).content)
    print(concepts_for_exam)
    print("=="*30)
    return {"concepts_for_exam":concepts_for_exam}

def refine_problems(state: AgentState):
    concepts_for_exam = state["concepts_for_exam"]
    personality = state["personality"]
    problems = []
    for concept in concepts_for_exam:
        problems.append(llm.invoke(REFINE_PROBLEMS_PROMPT.format(personality=personality, concept=concept)).content)
    
    return {"problems":problems}

def save_exam(state: AgentState):
    title = os.path.basename(state["exam_docs_path"])
    user_id = state["user_id"]
    user_dir = f"{user_id}/exam/"
    problems= "\n".join(state["problems"])

    os.makedirs(user_dir, exist_ok=True)
    with open(os.path.join(user_dir,f"{title}_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.md"), "w", encoding="utf-8") as md_file:
        md_file.write(problems)

    print(problems)
    messages = state["messages"]
    messages.append(AIMessage(content=problems))
    
    return {"messages":messages}