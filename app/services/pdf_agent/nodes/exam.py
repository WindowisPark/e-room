# app/services/pdf_agent/nodes/exam.py

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.pdf_agent.states import AgentState
from gptpdf import parse_pdf
from langchain_core.messages import HumanMessage
from app.services.pdf_agent.utils.file_utils import save_output_file, get_file_info, cleanup_old_files
import os
import mimetypes
import base64
import logging

logger = logging.getLogger(__name__)
llm = ChatOpenAI(model="gpt-4.1-mini")

def start_point_of_exam(state: AgentState):
    print("시험 그래프 시작")

def get_image_data(image_path):
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        mime_type = "image/jpeg"
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
    return f"data:{mime_type};base64,{base64_image}"

def analyze_previous_exam(state: AgentState):
    paths = state["previous_exam_path"]
    index = state.get("previous_exam_index", 0)
    now_path = paths[index]

    output_path = "images"
    content, images = parse_pdf(now_path, output_path=output_path, model="gpt-4.1-nano")

    splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
    chunks = splitter.create_documents([content])

    image_explanation = {}
    pdf_check_idx = 0
    for image in images:
        for pdf_idx in range(pdf_check_idx, len(chunks)):
            if image in chunks[pdf_idx].page_content:
                pdf_check_idx = pdf_idx
                image_path = os.path.join(output_path, image)
                messages = [
                    SystemMessage(content="이미지 설명 전문가로서 글과 이미지 기반 설명을 생성해주세요."),
                    HumanMessage(content=[
                        {"type": "text", "text": "이미지를 설명해주세요."},
                        {"type": "image_url", "image_url": {"url": get_image_data(image_path)}}
                    ])
                ]
                explanation = llm.invoke(messages).content
                image_explanation[image] = explanation
                break

    result = llm.invoke(f"""
    다음은 기출 문제입니다. 출제자의 성향을 분석해주세요. 핵심 위주, 지엽적, 고난이도 등 가능.
    이미지 설명(json)도 함께 참고하세요.
    문제: {content}
    이미지 설명: {image_explanation}
    """).content

    personality = state.get("personality", {})
    personality[index] = result

    return {"personality": personality, "previous_exam_index": index + 1}

def check_exam_count(state: AgentState):
    index = state.get("previous_exam_index", 0)
    paths = state.get("previous_exam_path", [])
    
    print(f"[exam] check_exam_count: index={index}, total={len(paths)}")

    if not isinstance(paths, list) or index >= len(paths):
        return "completion"
    return "continue"

def final_personality(state: AgentState):
    personality = state["personality"]
    result = llm.invoke(f"여러 기출 성향을 종합하여 출제자의 성향을 분석해주세요.\n{personality}").content
    return {"final_personality": result}

def get_concept_for_exam(state: AgentState):
    pdf_text = state["pdf_text"]
    personality = state["final_personality"]

    splitter = RecursiveCharacterTextSplitter(chunk_size=5000, chunk_overlap=500)
    chunks = splitter.create_documents([pdf_text])

    concepts = ""
    for chunk in chunks:
        concepts += llm.invoke(f"""
        당신은 {personality} 성격의 출제자입니다.
        다음 내용을 보고 출제하고 싶은 개념들을 이유와 함께 정리해주세요.
        내용 : {chunk.page_content}
        """).content

    return {"concepts_for_exam": concepts}

def refine_problems(state: AgentState):
    """개선된 시험문제 생성 및 저장"""
    concepts = state["concepts_for_exam"]
    personality = state["final_personality"]
    user_id = state["user_id"]
    total = len(concepts)
    problem = ""

    # 시험문제 생성
    for i in range(0, total, 18000):
        part = concepts[i:i+20000]
        problem += llm.invoke(f"""
        당신은 {personality} 성격의 시험 출제자입니다.
        아래 내용을 참고하여 시험 문제 10~20개를 생성해주세요.
        난이도 비율은 Easy:Medium:Hard = 3:5:2 로 해주세요.
        내용: {part}
        """).content

    try:
        # ✅ 새로운 유틸리티 사용
        file_path, filename = save_output_file(
            user_id=user_id,
            task_type="exam",
            content=problem,
            file_format="md"
        )
        
        # 파일 정보 가져오기
        file_info = get_file_info(file_path)
        
        # 오래된 파일 정리 (최신 3개만 유지)
        deleted_count = cleanup_old_files(user_id, "exam", keep_count=3)
        if deleted_count > 0:
            logger.info(f"시험문제 파일 {deleted_count}개 정리됨 (사용자: {user_id})")
        
        logger.info(f"시험문제 파일 저장 완료: {file_path}")
        
        return {
            "result": problem,
            "saved_path": file_path,
            "saved_filename": filename,
            "file_info": file_info
        }
        
    except Exception as e:
        logger.error(f"시험문제 파일 저장 실패: {str(e)}")
        return {
            "result": problem,
            "error": f"파일 저장 실패: {str(e)}"
        }

def select_previous_exam(state: AgentState):
    """
    기출문제 경로가 없으면 사용자에게 업로드 요청 메시지 삽입
    """
    if not state.get("previous_exam_path"):
        message = HumanMessage(content="기출문제 파일을 업로드해주세요. 예: '기출_2023_정보보안.pdf'")
        messages = state.get("messages", [])
        messages.append(message)
        return {
            "messages": messages,
            "waiting_for_exam_file": True  # 상태 표시
        }
    return {}  # 문제 없으면 다음으로 진행

def check_exist_previous_exam(state: AgentState):
    """
    기출문제 유무에 따라 흐름 분기 (경로 유효성까지 포함)
    """
    previous_exam_path = state.get("previous_exam_path")

    if not previous_exam_path:
        return "no_exist"

    import os

    # 문자열이면 하나의 파일 경로
    if isinstance(previous_exam_path, str):
        return "exist" if os.path.exists(previous_exam_path) else "no_exist"

    # 리스트인 경우 하나라도 유효하면 exist
    if isinstance(previous_exam_path, list):
        if any(os.path.exists(path) for path in previous_exam_path if path):
            return "exist"
        return "no_exist"

    return "no_exist"

def get_final_personality(state: AgentState):
    personality = state["personality"]
    result = llm.invoke(f"여러 기출 성향을 종합하여 출제자의 성향을 분석해주세요.\n{personality}").content
    return {"final_personality": result}

def get_all_files(state: AgentState):
    """
    학습용 PDF 파일이 필요할 때 사용자에게 업로드 요청
    """
    message = HumanMessage(content="시험 문제 생성을 위해 학습할 PDF 파일을 업로드해주세요.")
    messages = state.get("messages", [])
    messages.append(message)
    return {
        "messages": messages,
        "waiting_for_study_file": True
    }

def simple_problem_generation(state: AgentState):
    """기출문제 없을 때 간단한 시험문제 생성"""
    user_prompt = state["messages"][-1].content
    material = state.get("pdf_text") or state.get("summaries") or "자료가 충분하지 않습니다."
    user_id = state["user_id"]

    prompt = f"""
다음 학습 자료를 기반으로 시험 문제를 생성해주세요.

요구사항:
- 총 10문제
- 난이도 구성: 쉬움(Easy) 3문제, 보통(Medium) 5문제, 어려움(Hard) 2문제
- 문제 유형 구성: 객관식(Multiple Choice) 5문제, 주관식(Short Answer) 5문제
- 모든 문제는 아래 형식을 따르세요:

형식 예시:
문제 1. (난이도: Easy / 유형: 객관식)
다음 중 정보보호의 기본 요소가 아닌 것은?
A. 기밀성
B. 무결성
C. 가용성
D. 가독성

문제 2. (난이도: Medium / 유형: 주관식)
공개키 암호 방식의 개념과 장단점을 서술하시오.

학습 자료:
{material}

사용자 요청: {user_prompt}

시험 문제를 생성해주세요.
"""

    result = llm.invoke(prompt).content

    try:
        # ✅ 새로운 유틸리티 사용
        file_path, filename = save_output_file(
            user_id=user_id,
            task_type="exam",
            content=result,
            file_format="md"
        )
        
        # 파일 정보 가져오기
        file_info = get_file_info(file_path)
        
        logger.info(f"간단 시험문제 파일 저장 완료: {file_path}")
        
        return {
            "result": result,
            "saved_path": file_path,
            "saved_filename": filename,
            "file_info": file_info,
            "messages": state["messages"] + [HumanMessage(content=result)]
        }
        
    except Exception as e:
        logger.error(f"간단 시험문제 파일 저장 실패: {str(e)}")
        return {
            "result": result,
            "messages": state["messages"] + [HumanMessage(content=result)],
            "error": f"파일 저장 실패: {str(e)}"
        }