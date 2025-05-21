# app/services/pdf_agent/nodes/summary.py

from app.services.pdf_agent.states import AgentState
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from dotenv import load_dotenv
from app.services.pdf_agent.chromadb_service import ChromaDBService  # ✅ tools 제거, chroma 사용
import json
import os

load_dotenv()
llm = ChatOpenAI(model="gpt-4.1-mini")

def start_point_of_summary(state: AgentState):
    print("요약 그래프 시작")


def get_related_pdf(state: AgentState):
    """
    관련 문서 검색
    - 사용자 ID와 폴더명을 기반으로 ChromaDB에서 유사 문서 검색
    - 사용자 질문을 기준으로 query_text 전달
    """
    messages = state["messages"]
    require = messages.pop().content
    user_id = int(state["user_id"])
    folder = state.get("folder", "default")

    chroma = ChromaDBService()
    docs = chroma.search_across_documents(
        user_id=user_id,
        query_text=require,
        folder_name=folder,
        limit=1
    )

    if not docs:
        raise ValueError(f"관련 PDF 문서를 찾을 수 없습니다. user_id={user_id}, folder={folder}, query='{require}'")

    return {"pdf_content": docs[0]}


def pdf_parsing(state: AgentState):
    """
    텍스트 청크 분할
    - LangChain의 RecursiveCharacterTextSplitter 사용
    """
    pdf_content = state["pdf_content"]
    text = pdf_content.get("text", "") if isinstance(pdf_content, dict) else str(pdf_content)

    print(f"PDF 파싱: 텍스트 길이 = {len(text)}")
    doc = Document(page_content=text)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=4000, chunk_overlap=400)

    try:
        chunks = text_splitter.split_documents([doc])
        print(f"텍스트 분할 완료: {len(chunks)}개 청크 생성됨")
        return {"pdfs": chunks, "pdf_step": 0}
    except Exception as e:
        print(f"텍스트 분할 오류: {str(e)}")
        return {"pdfs": [], "pdf_step": 0, "error": str(e)}


def check_summary_completion(state: AgentState):
    """
    모든 PDF 청크가 요약되었는지 확인
    """
    pdfs = state.get("pdfs", [])
    now_step = state.get("pdf_step", 0)
    print(f"요약 진행 상황: {now_step}/{len(pdfs)}")

    if not pdfs or now_step >= len(pdfs):
        return "completion"
    return "continue"


def summary_pdf(state: AgentState):
    """
    청크별 요약 생성
    """
    pdfs = state.get("pdfs", [])
    step = state.get("pdf_step", 0)
    summaries = state.get("summaries", "")

    if step >= len(pdfs):
        return {"pdf_step": step, "summaries": summaries}

    try:
        pdf = pdfs[step]
        text = pdf.page_content
        print(f"요약 시작: 청크 {step}, 길이 {len(text)}")
        result = llm.invoke(f"다음 내용을 빠짐없이 요약해주세요.\n\n내용 : {text}")
        summaries += result.content
    except Exception as e:
        print(f"요약 오류: {str(e)}")
        summaries += f"[요약 실패: {str(e)}]"

    return {"pdf_step": step + 1, "summaries": summaries}


def refine_textbook(state: AgentState):
    """
    요약본을 마크다운 기반 학습자료로 변환
    """
    summaries = state["summaries"]
    result = llm.invoke(f"""
    다음 내용을 기반으로 마크다운 학습자료를 만들어주세요. 삭제 없이 보기 좋게 정리해주세요.
    내용 : {summaries}
    """).content
    return {"result": result}


def get_need_to_explain(state: AgentState):
    """
    요약 결과 중 배경지식이 필요한 키워드 추출 (json)
    """
    result = state["result"]
    prompt = (
        "다음 내용에서 배경지식이 필요한 단어를 예시와 같은 json 형식으로 정리해주세요. "
        '예: {"단어1": "이유", ...}'
    )
    response = llm.invoke(f"{prompt}\n내용: {result}")
    return {"need_to_explain": json.loads(response.content)}


def check_explain_completion(state: AgentState):
    """
    배경지식 설명 루프 종료 판단
    """
    total = len(state["need_to_explain"])
    now = state["explain_step"]
    return "continue" if now < total else "completion"


def explain(state: AgentState):
    """
    개별 키워드에 대한 배경지식 설명 생성
    """
    need_to_explain = state["need_to_explain"]
    now = state["explain_step"]
    key = list(need_to_explain.keys())[now]
    reason = list(need_to_explain.values())[now]

    question = f"{reason}를 고려하여 '{key}'를 간단히 설명해주세요."
    explanation = llm.invoke(question).content
    need_to_explain[key] = explanation

    return {"explain_step": now + 1, "need_to_explain": need_to_explain}


def add_explaination(state: AgentState):
    """
    배경지식 설명을 원문에 각주 형식으로 추가
    """
    result = state["result"]
    references = state["need_to_explain"]
    response = llm.invoke(f"""
    아래 내용에 참고자료(각주)를 markdown 형식으로 추가해주세요.
    내용: {result}
    참고자료: {references}
    """).content
    return {"result": response}


def gen_sample_question(state: AgentState):
    """
    요약 내용을 기반으로 간단한 주관식 문제 생성
    """
    result = state["result"]
    exam = llm.invoke(f"다음 내용을 잘 이해했는지 확인할 수 있는 간단한 주관식 문제를 만들어주세요.\n\n내용: {result}").content
    return {"result": result + "\n\n" + exam}


def save_file(state: AgentState):
    """
    최종 결과를 마크다운 파일로 저장
    """
    result = state["result"]
    user_id = state["user_id"]
    output_dir = f"{user_id}/summary"
    os.makedirs(output_dir, exist_ok=True)
    file_index = len(os.listdir(output_dir)) + 1
    output_path = os.path.join(output_dir, f"output{file_index}.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(result)
