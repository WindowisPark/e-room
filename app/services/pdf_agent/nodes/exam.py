# app/services/pdf_agent/nodes/exam.py

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.pdf_agent.states import AgentState
from gptpdf import parse_pdf
import os
import mimetypes
import base64

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
    if state["previous_exam_index"] >= len(state["previous_exam_path"]):
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
    concepts = state["concepts_for_exam"]
    personality = state["final_personality"]
    total = len(concepts)
    problem = ""

    for i in range(0, total, 18000):
        part = concepts[i:i+20000]
        problem += llm.invoke(f"""
        당신은 {personality} 성격의 시험 출제자입니다.
        아래 내용을 참고하여 시험 문제 10~20개를 생성해주세요.
        난이도 비율은 Easy:Medium:Hard = 3:5:2 로 해주세요.
        내용: {part}
        """).content

    with open("problem.md", "w", encoding="utf-8") as f:
        f.write(problem)

    return {"result": problem}
