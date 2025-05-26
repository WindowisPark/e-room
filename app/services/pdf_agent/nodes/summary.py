# app/services/pdf_agent/nodes/summary.py

from app.services.pdf_agent.states import AgentState
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from dotenv import load_dotenv
from app.services.pdf_agent.tools import search_documents_for_summary  # ✅ ChromaDBService 제거하고 tools 기반으로 교체
from app.services.pdf_agent.utils.file_utils import save_output_file, get_file_info, cleanup_old_files
import json
import os
import logging

load_dotenv()
llm = ChatOpenAI(model="gpt-4.1-mini")
logger = logging.getLogger(__name__)

def start_point_of_summary(state: AgentState):
    print("요약 그래프 시작")

def get_related_pdf(state: AgentState):
    messages = state["messages"]
    request = messages.pop().content
    user_id = state["user_id"]
    folder = state.get("folder", "default")

    refined_query = llm.invoke(f"""
    사용자의 요청은 문서 요약입니다.
    이 요청에서 핵심 키워드를 한두 단어로 추출하세요.

    요청: "{request}"
    """).content.strip()

    pdfs = search_documents_for_summary(
        user_id=user_id,
        folder=folder,
        query=refined_query,
        k=5
    )

    if not pdfs:
        raise ValueError(f"관련 문서를 찾을 수 없습니다. refined_query='{refined_query}'")

    full_text = "\n".join(p.page_content for p in pdfs)
    return {"pdf_content": {"text": full_text}}

def pdf_parsing(state: AgentState):
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
    pdfs = state.get("pdfs", [])
    now_step = state.get("pdf_step", 0)

    print(f"요약 진행 상황: {now_step}/{len(pdfs)}")

    if not isinstance(pdfs, list) or len(pdfs) == 0:
        print("[check_completion] pdfs가 없어서 종료")
        return "completion"

    if now_step >= len(pdfs):
        return "completion"

    return "continue"

def summary_pdf(state: AgentState):
    pdfs = state.get("pdfs", [])
    step = state.get("pdf_step", 0)
    summaries = state.get("summaries", "")

    if not isinstance(pdfs, list) or step >= len(pdfs):
        print(f"[summary_pdf] 스킵: step={step}, pdfs 길이={len(pdfs)}")
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
    summaries = state["summaries"]
    result = llm.invoke(f"""
    다음 내용을 기반으로 마크다운 학습자료를 만들어주세요. 삭제 없이 보기 좋게 정리해주세요.
    내용 : {summaries}
    """).content
    return {"result": result}

def get_need_to_explain(state: AgentState):
    result = state["result"]
    prompt = (
        "다음 내용에서 배경지식이 필요한 단어를 예시와 같은 json 형식으로 정리해주세요. "
        '예: {"단어1": "이유", ...}'
    )

    response = llm.invoke(f"{prompt}\n내용: {result}")
    content = response.content.strip()

    try:
        if content.startswith("```") and content.endswith("```"):
            content = content.strip("```").strip()
        if content.startswith("json"):
            content = content[4:].strip()

        parsed = json.loads(content)

        return {
            "need_to_explain": parsed,
            "explain_step": 0
        }

    except Exception as e:
        logger.error(f"[요약] JSON 파싱 실패: {e} / 응답: {content}")
        return {"need_to_explain": {}}

def check_explain_completion(state: AgentState):
    total = len(state["need_to_explain"])
    now = state["explain_step"]
    return "continue" if now < total else "completion"

def explain(state: AgentState):
    need_to_explain = state["need_to_explain"]
    now = state["explain_step"]

    if not need_to_explain or now >= len(need_to_explain):
        return {"explain_step": now, "need_to_explain": need_to_explain}

    key = list(need_to_explain.keys())[now]
    reason = list(need_to_explain.values())[now]

    question = f"{reason}를 고려하여 '{key}'를 간단히 설명해주세요."
    explanation = llm.invoke(question).content
    need_to_explain[key] = explanation

    return {"explain_step": now + 1, "need_to_explain": need_to_explain}

def add_explaination(state: AgentState):
    result = state["result"]
    references = state["need_to_explain"]
    response = llm.invoke(f"""
    아래 내용에 참고자료(각주)를 markdown 형식으로 추가해주세요.
    내용: {result}
    참고자료: {references}
    """).content
    return {"result": response}

def gen_sample_question(state: AgentState):
    result = state["result"]
    exam = llm.invoke(f"다음 내용을 잘 이해했는지 확인할 수 있는 간단한 주관식 문제를 만들어주세요.\n\n내용: {result}").content
    return {"result": result + "\n\n" + exam}

def save_file(state: AgentState):
    """개선된 파일 저장 함수"""
    result = state["result"]
    user_id = state["user_id"]
    
    try:
        # ✅ 새로운 유틸리티 사용
        file_path, filename = save_output_file(
            user_id=user_id,
            task_type="summary",
            content=result,
            file_format="md"
        )
        
        # 파일 정보 가져오기
        file_info = get_file_info(file_path)
        
        # 오래된 파일 정리 (최신 5개만 유지)
        deleted_count = cleanup_old_files(user_id, "summary", keep_count=5)
        if deleted_count > 0:
            logger.info(f"요약 파일 {deleted_count}개 정리됨 (사용자: {user_id})")
        
        logger.info(f"요약 파일 저장 완료: {file_path}")
        
        return {
            **state,
            "saved_path": file_path,
            "saved_filename": filename,
            "file_info": file_info
        }
        
    except Exception as e:
        logger.error(f"요약 파일 저장 실패: {str(e)}")
        return {
            **state,
            "error": f"파일 저장 실패: {str(e)}"
        }