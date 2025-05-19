from dotenv import dotenv_values
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_upstage import UpstageDocumentParseLoader
from langchain_text_splitters import CharacterTextSplitter,RecursiveCharacterTextSplitter
from langchain_core.messages import HumanMessage,SystemMessage
from states import AgentState
from gptpdf import parse_pdf
import mimetypes
import base64
import os
import json
from tools import search_documents_for_exam

envs = dotenv_values(".env")
api_key = envs["OPENAI_API_KEY"]
llm = ChatOpenAI(model = "gpt-4.1-mini")

def start_point_of_exam(state : AgentState):
    print("시험 그래프 시작")

def select_previous_exam(state : AgentState):
    previous_exam_path = input("기출 문제 경로를 입력해주세요.(띄어쓰기로 구분)").split() # 파일 경로임
    return {"previous_exam_path":previous_exam_path,"previous_exam_index":0}


def get_image_data(image_path):
    # 이미지 파일 확장자로부터 MIME 타입 추론
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        mime_type = "image/jpeg"  # 기본값

    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode('utf-8')

    return f"data:{mime_type};base64,{base64_image}"

def analyze_previous_exam(state:AgentState): # 과거 시험 문제 병합 및 파일
    previous_exam = state["previous_exam_path"]
    previous_exam_index = state["previous_exam_index"]
    now_exam_file_path = previous_exam[previous_exam_index]

    output_path = "images" # 경로 수정 필요할듯

    content, images = parse_pdf(now_exam_file_path,  output_path=output_path,model="gpt-4.1-nano",api_key=api_key)
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=5000,
        chunk_overlap=500,
        length_function=len,
        is_separator_regex=False,
    )
    pdfs = text_splitter.create_documents([content]) # 분할
    image_explanation = {}
    pdf_check_idx = 0
    for image_idx in range(len(images)) :
        for pdf_idx in range(pdf_check_idx,len(pdfs)) :
            if(images[image_idx] in pdfs[pdf_idx].page_content) : # 해당 페이지 내용에 image가 있다면
                pdf_check_idx = pdf_idx
                image_path = os.path.join(output_path,images[image_idx])
                messages = [
                    SystemMessage(content="당신은 글을 읽고 이미지에 대한 적절한 설명을 해주는 전문가입니다. 당신은 글과 이미지 분석에 대한 일가견이 있습니다. 이미지는 글 안에 포함이 되어 있으며 이미지가 이용된 경우 경로로 표시되어 있습니다. 사용자가 글만 읽어도 이해할 수 있도록 이미지에 대한 적절한 설명을 글과 어울리게 작성해주세요."),
                    HumanMessage(
                        content=[
                            {"type": "text", "text": "첨부한 이미지가 어떤 이미지인지 글과 관련하여 설명해주세요."},
                            {
                                "type": "image_url",
                                "image_url": {"url": get_image_data(image_path)},
                            },
                        ],
                    )
                ]
                result = llm.invoke(messages).content
                image_explanation[images[image_idx]] = result # 이미지 번호 : 이미지 설명 json 저장
                break # 한 번 나왔으면 뒤에선 안나오니까 종료

    result = llm.invoke(f"""다음 시험 문제를 참고하여 출제자의 성향을 분석해주세요. 이때 성향은 핵심 개념 위주, 지엽적인 설명 위주, 쉬운 문제 위주, 고난이도 문제 위주 등 다양한 성향이 있을 수 있으며 다음 시험 문제 출제자가 참고하기 좋도록 작성하여 주세요.
               \n시험 문제와 별도로 첨부된 json형식의 글은 시험 문제 내용 중 포함된 이미지에 대한 설명을 이미지 경로(key)와 설명(value)로 표현한 파일입니다. json 형식의 글을 참고하여 시험 문제를 이해해주세요.
               \n시험 문제 : {content}
               \njson : {image_explanation}""").content

    personality = state["personality"]

    personality[previous_exam_index] = result

    return {"personality":personality,"previous_exam_index":previous_exam_index+1}

def check_exam_count(state: AgentState):
    previous_exam_index = state["previous_exam_index"]

    if previous_exam_index == len(state["previous_exam"]):
        return "completion"
    else:
        return "continue"

def final_personality(state: AgentState):
    personality = state["personality"]
    result = llm.invoke(f"다음 내용은 같은 출제자의 여러 시험의 각 성향을 분석한 내용입니다. 다음 내용을 참고하여 종합적인 출제자의 성향을 분석해주세요. \n{personality}").content
    return {"final_personality" : result}

def get_all_files(state: AgentState):
    pdfs = search_documents_for_exam(state["user_id"],state["folder"])
    return {"pdfs" : pdfs, "pdf_step" : 0}

def get_concept_for_exam(state: AgentState):
    ## LLM Query해서 요약본 파일 GET한게 result라 가정
    pdfs = state["pdfs"]
    pdf = pdfs[state["pdf_step"]]
    problem = ""
    personality = state["final_personality"]
    concepts_for_exam = ""

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=5000,
        chunk_overlap=500,
        length_function=len,
        is_separator_regex=False,
    )
    pdfs = text_splitter.create_documents([result]) # 분할
    for pdf in pdfs:
        concepts_for_exam += llm.invoke(f"""당신은 {personality} 성격을 가진 시험 출제위원입니다.\n
                주어진 다음 내용을 보고 다음 내용에서 본인의 출제 성격에 맞춰 시험에 낼만한 내용 및 개념들을 이유와 함께 정리해주세요.\n
                문제를 생성하는 것이 아닌 출제하고 싶은 내용을 정리하는 것입니다.\n
                내용 : {pdf.page_content}
                """)
    return {"concepts_for_exam":concepts_for_exam}

def refine_problems(state: AgentState):
    concepts_for_exam = state["concepts_for_exam"]
    personality = state["personality"]
    total_length = len(concepts_for_exam)
    # 총 30문제를 만드는게 목적임
    ## 10000자 단위로 분할하여 반복 시킬 예쩡
    problem = ""
    for length in range(0,total_length,18000):
        problem += llm.invoke(f"""당신은 {personality} 성격을 가진 시험 문제 출제 위원입니다.
                제공된 내용은 시험에 내고 싶은 개념 및 내용과 이유입니다. 내용을 참고하여 시험 범위, 출제 이유, 필요한 학습 개념과 함께 시험 문제 10개~20개를 생성해주세요.
                각 내용은 결합되어도 됩니다. 예를 들어, A개념과 B개념 2가지가 적혀있는데 이 둘을 결합한 한 문제를 제작해주는 것은 괜찮습니다.

                생성하는 시험 문제의 난이도 비율(Easy:Medium:Hard)은 3:5:2로 생성해주세요.

                내용 : {concepts_for_exam[length : length + 20000]}""")


    with open("problem.md", "w", encoding="utf-8") as md_file:
        md_file.write(problem)
