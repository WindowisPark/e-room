# app/services/pdf_agent/nodes/summary.py

from app.services.pdf_agent.states import AgentState
from langchain.retrievers.multi_query import MultiQueryRetriever
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
from langchain_text_splitters import CharacterTextSplitter, RecursiveCharacterTextSplitter
import fitz  # PyMuPDF
import wikipedia
import subprocess
import json

load_dotenv()

llm = ChatOpenAI(model="gpt-4.1-mini")

# LLM 응답 테스트용
def generate_response(state: AgentState):
    messages = state["messages"]
    response = llm.invoke(messages)
    return {"messages": messages + [{"role": "assistant", "content": response.content}]}


# PDF 파싱
def pdf_parsing(state: AgentState):
    pdf_path = state["pdf_path"]
    doc = fitz.open(pdf_path)
    all_text = "\n".join([page.get_text() for page in doc])
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=3000,
        chunk_overlap=300,
        length_function=len,
        is_separator_regex=False,
    )
    pdfs = text_splitter.create_documents([all_text])
    return {"pdfs": pdfs}


# 요약 개수 확인
def check_summary_completion(state: AgentState):
    total_step = len(state["pdfs"])
    now_step = state["pdf_step"]
    print(f"{now_step}/{total_step}")
    return "continue" if total_step > now_step else "completion"


# pdf 요약
def summary_pdf(state: AgentState):
    step = state["pdf_step"]
    summaries = state["summaries"]
    pdf = state["pdfs"][step]
    result = llm.invoke(f"다음 내용을 전반적으로 빠지는 것 없도록 상세하게 요약해주세요. \n\n내용 : {pdf}")
    summaries += result.content
    return {"pdf_step": step + 1, "summaries": summaries}


# text book으로 재구성
def refine_textbook(state: AgentState):
    summaries = state["summaries"]
    result = llm.invoke(f"다음 내용을 기반으로 마크다운을 활용하여 정리된 하나의 교육자료를 제공해주세요. 내용을 학습자료로서 보기 좋게 구성해주되, 내용의 삭제는 이루어지면 안됩니다. \n\n내용 : {summaries}").content
    return {"result": result}


# 배경지식 설명 필요한거 찾기
def get_need_to_explain(state: AgentState):
    result = state["result"]
    example = '{"단어 1":"단어 1 설명이 필요한 이유",...}'
    need_to_explain = llm.invoke(
        f"다음 내용 중 배경 지식이 필요한 요소를 이유와 함께 예시와 같은 json 형식으로만 정리해주세요. "
        f"다른 백틱이나 용어가 들어가면 안 됩니다. dict로 바로 변환할 수 있도록 json형식으로 출력해주세요. \nex) {example} \n 내용 : {result}"
    )
    return {"need_to_explain": json.loads(need_to_explain.content)}


# 설명 개수 확인
def check_explain_completion(state: AgentState):
    total_step = len(state["need_to_explain"])
    now_step = state["explain_step"]
    print(f"{now_step}/{total_step}")
    return "continue" if total_step > now_step else "completion"


# 설명 시작 (Wikipedia API 기반)
def explain(state: AgentState):
    need_to_explain = state["need_to_explain"]
    now_step = state["explain_step"]
    key = list(need_to_explain.keys())[now_step]
    value = list(need_to_explain.values())[now_step]

    try:
        wiki_summary = wikipedia.summary(key, sentences=3, auto_suggest=False)
    except Exception:
        wiki_summary = f"{key}에 대한 Wikipedia 검색 실패. LLM 설명으로 대체합니다."
        result = llm.invoke(f"{value}를 위해 {key}에 대한 설명이 필요합니다. {key}를 간단히 설명해주세요.")
        wiki_summary += "\n\n" + result.content

    need_to_explain[key] = wiki_summary
    return {"explain_step": now_step + 1, "need_to_explain": need_to_explain}


# 설명 본문에 추가
def add_explain(state: AgentState):
    result = state["result"]
    need_to_explain = state["need_to_explain"]
    final_result = llm.invoke(
        f"다음 내용에 참고자료를 이용하여 설명을 추가한 최종 내용을 작성해주세요. 조건은 다음과 같습니다.\n"
        f"1. 기존 내용은 삭제하거나 변경해서는 안 됨 (각주 표기 추가는 허용)\n"
        f"2. 각주 설명은 markdown형식을 활용하여 각 설명이 필요한 부분이 나타난 아래 문단에 추가 \n"
        f"내용 : {result} \n참고자료 : {need_to_explain}"
    )
    return {"result": final_result.content}


# 학습 테스트용 문제 생성
def gen_sample_question(state: AgentState):
    result = state["result"]
    exam = llm.invoke(
        f"다음 내용은 제가 제작한 학습 자료입니다. 마크다운을 활용하여 학생들이 학습 자료를 잘 공부하였는지 확인하기 위한 간단한 주관식 문제를 제작해주세요. "
        f"전반적으로 모든 내용을 검사할 수 있도록 제작해주세요. 내용 : {result}"
    )
    return {"result": result + exam.content}


# PDF 추출
def extract_pdf(state: AgentState):
    result = state["result"]
    with open("output.md", "w", encoding="utf-8") as md_file:
        md_file.write(result)
    subprocess.run(["pandoc", "output.md", "-o", "output.pdf"])
