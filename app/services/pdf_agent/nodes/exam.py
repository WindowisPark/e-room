# from states import AgentState
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_upstage import UpstageDocumentParseLoader
load_dotenv()
llm = ChatOpenAI(model = "gpt-4.1-mini")
# 시험 문제 생성의 흐름
## 1. 기존 기출 문제 출제자 성향 분석 ( 전체 데이터 입력 )
## 2. 성향을 3가지 정도로 파악 (지엽적, 핵심 개념 위주, 고난도 문제 위주)
## 3. 가장 성향이 잘 드러나는 문제 N개 수집 
## 4. 문제 N개와 성향을 참고하여 시험 문제 JSON형태로 생성 ( 분할된 Documnet당 K개씩 )
## 5. 생성된 문제 JSON형태의 문제들을 모두 결합하여 하나의 변수에 추가한 뒤, markdown으로 재구성
## 6. 재구성된 시험문제 PDF로 출력

def get_document(file_path: str):
    loader = UpstageDocumentParseLoader(
        file_path=file_path,
        output_format="markdown",
        split="page",
        ocr="force",
        coordinates=False
    )
    docs = loader.load()
    return docs

def get_exam_document():
    file_path = "test.pdf"
    docs = get_document(file_path)
    full_text = ""
    for doc in docs :
        full_text+= doc["page_content"]
    parsed_text = [] # 글자수 30000자 단위로 분할하여 처리하도록 하기 위함
    while True:
        if len(full_text)>30000:
            parsed_text.append(full_text[:30000])
            full_text = full_text[27000:]
        else :
            parsed_text.append(full_text)
            break
    return parsed_text

def analyze_exam():
    parsed_text = get_exam_document()
    analysis = llm.invoke(f"다음 본문은 과거 출제된 시험 문제입니다. 시험 문제지의 주요 특성을 3가지(지엽적인 내용 위주, 핵심 개념 위주, 고난이도 내용 위주) 중 하나로 분류하고, 출제자의 성향을 분석한 코멘트를 작성해주세요. \n\n본문 : {parsed_text}")

def generate_exam():
    analysis = ""
    problems = llm.invoke(f"다음은 출제자의 성향에 관한 코멘트입니다. 출제자의 성향을 바탕으로 문제를 5개 생성하여 json형식으로 답변해주세요. 바로 json으로 변환할 수 있게 json형식으로만 답변해주시면 됩니다.")


if __name__ =="__main__":
    print(get_document())