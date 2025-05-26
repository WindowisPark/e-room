# app/services/pdf_agent/nodes/exam.py

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.services.pdf_agent.states import AgentState
from langchain_community.document_loaders import PDFPlumberLoader
from datetime import datetime
import os
import mimetypes
import base64

llm = ChatOpenAI(model="gpt-4.1-mini")

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
        result = llm.invoke(f"""다음 시험 문제를 참고하여 출제자의 성향을 분석해주세요. 
                            이때 성향은 핵심 개념 위주, 지엽적인 설명 위주, 쉬운 문제 위주, 고난이도 문제 위주 등 다양한 성향이 있을 수 있으며 다음 시험 문제 출제자가 참고하기 좋도록 작성하여 주세요.
                \n시험 문제 : {full_text} 
                    """).content
        personality.append(result)
        print("=====출제자의 성향=====")
        print(personality)
    
    return {"personality":personality}

def get_final_personality(state: AgentState):
    personality = state["personality"]
    result = llm.invoke(f"다음 성향 리스트는 같은 출제자의 여러 시험의 각 성향을 분석한 내용입니다. 다음 내용을 참고하여 종합적인 출제자의 성향을 분석해주세요. \n성향 : {personality}").content
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
        concepts_for_exam.append(llm.invoke(f"""당신은 {personality} 성격을 가진 시험 출제위원입니다.\n
                주어진 다음 내용을 보고 다음 내용에서 본인의 출제 성격에 맞춰 시험에 낼만한 내용 및 개념들을 이유와 함께 정리해주세요.\n
                문제를 생성하는 것이 아닌 출제하고 싶은 내용을 정리하는 것입니다.\n
                내용 : {pdf.page_content}
                """).content)
    print(concepts_for_exam)
    print("=="*30)
    return {"concepts_for_exam":concepts_for_exam}

def refine_problems(state: AgentState):
    concepts_for_exam = state["concepts_for_exam"]
    personality = state["personality"]
    problems = []
    for concept in concepts_for_exam:
        problems.append(llm.invoke(f"""당신은 {personality} 성격을 가진 시험 문제 출제 위원입니다.
                제공된 내용은 시험에 내고 싶은 개념 및 내용과 이유입니다. 내용을 참고하여 시험 범위, 출제 이유, 필요한 학습 개념과 함께 시험 문제 10개를 생성해주세요.
                각 내용은 결합되어도 됩니다. 예를 들어, A개념과 B개념 2가지가 적혀있는데 이 둘을 결합한 한 문제를 제작해주는 것은 괜찮습니다.
                                    
                생성하는 시험 문제의 난이도 비율(Easy:Medium:Hard)은 3:5:2로 생성해주세요. 
                                  
                다른 설명과 같은 말은 하지 마시고, 시험 문제만 1~10번까지 10개 생성해주시면 됩니다.
                내용 : {concept}""").content)
    
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