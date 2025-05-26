# app/services/pdf_agent/nodes/summary.py

from app.services.pdf_agent.states import AgentState
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from dotenv import load_dotenv
from app.services.pdf_agent.tools import get_all_docs  # ✅ ChromaDBService 제거하고 tools 기반으로 교체
import json
import os
import logging
from tqdm import tqdm
from datetime import datetime

load_dotenv()
llm = ChatOpenAI(model="gpt-4.1-mini")
logger = logging.getLogger(__name__)

def start_point_of_summary(state: AgentState):
    print("요약 그래프 시작")

def get_related_pdf(state : AgentState):
    pdf_path = state["pdf_path"]
    pdf = get_all_docs(pdf_path)
    return {"pdf_content":pdf}

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
    summaries = ""
    for pdf in tqdm(pdfs) :
        result = llm.invoke(f"""다음 내용 중 중요한 내용 위주로 상세하게  요약해주세요. 
                            이때 요약은 마크다운을 활용하여, 학습자료로서 보기 좋게 구성하여 학습자가 정리된 자료만 보고도 학습이 가능하도록 해야합니다.
                            개념만 간단하게 작성하는 것이 아닌, 요약된 내용만 보고도 전체 원본의 내용을 이해할 수 있을 정도로 상세하게 요약해주셔야 합니다. 
                            
                            내용 : {pdf}""").content
        summaries += result
    return {"result":summaries}


# 배경지식 설명 필요한거 찾기
def get_need_to_explain(state : AgentState) :
    result = state["result"]
    example = '{"단어 1":"단어 1 설명이 필요한 이유",...}'
    need_to_explain = llm.invoke(f"다음 내용 중 배경 지식이 필요한 요소를 이유와 함께 예시와 같은 json 형식으로만 정리해주세요. 다른 백틱이나 용어가 들어가면 안 됩니다. 바로 json으로 이용할 수 있도록 json형식으로만 출력해주세요. \nex) {example} \n 내용 : {result}")
    return { "need_to_explain" :json.loads(need_to_explain.content)}

def explain(state: AgentState):
    need_to_explain = state["need_to_explain"]
    result_map = {}
    for key,value in tqdm(need_to_explain.items()):
        question = f"{value}를 위해 {key}에 대한 설명이 필요합니다. {key}에 대해서 간단히 설명해주세요."
        explanation = llm.invoke(question).content
        result_map[key] = explanation

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
    final_result = ""
    for divided_result in tqdm(divided_results) :    
        final_result += llm.invoke(f"""이전 내용, 원문, 참고자료를 이용하여 설명을 추가한 최종 내용을 작성해주세요. 
                                조건은 다음과 같습니다.
                                   
                                1. 이전 내용의 말미와 원문의 도입부가 자연스럽게 이어지도록 작성 (EX, 이전 내용의 말미가 4번으로 끝났다면, 원문이 1번부터 시작해도 5번으로 변경하여 작성)
                                2. 1번 상황외의 경우 기존 내용은 삭제하거나 변경해서는 안 됨 원문을 그대로 보존해야만 함.
                                3. 각주 설명은 설명이 필요한 용어가 포함된 헤더 단락 바로 아래에 추가 
                                
                                1,2,3을 반드시 준수하여 원문을 작성해주시길 바랍니다.

                                원문 : {divided_result}
                                참고자료 : {need_to_explain}""").content
    
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
    exam = llm.invoke(f"다음 내용은 제가 제작한 학습 자료입니다. 마크다운을 활용하여 학생들이 학습 자료를 잘 공부하였는지 확인하기 위한 간단한 주관식 문제를 제작해주세요. 전반적으로 모든 내용을 검사할 수 있도록 제작해주세요. 내용 : {result}")
    return {"result":result+exam.content}

def save_file(state:AgentState):
    result = state["result"]
    user_id = state["user_id"]
    title = os.path.basename(state["pdf_path"])
    user_dir = f"{user_id}/summary" 
    os.makedirs(user_dir, exist_ok=True)
    with open(os.path.join(user_dir,f"{title}_final_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"), "w", encoding="utf-8") as md_file:
        md_file.write(result)
