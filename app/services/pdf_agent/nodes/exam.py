# app/services/pdf_agent/nodes/exam.py (get_all_docs 임포트 수정)

import os
import mimetypes
import base64
import logging
from datetime import datetime
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PDFPlumberLoader

from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.tools import get_all_docs  # ✅ 임포트 추가

logger = logging.getLogger(__name__)
llm = ChatOpenAI(model="gpt-4o-mini")

def start_point_of_exam(state: AgentState):
    print("시험 그래프 시작")
    return state

def select_previous_exam(state: AgentState):
    """기출 문제 경로 설정 (WebSocket에서는 이미 설정됨)"""
    previous_exam_path = state.get("previous_exam_path", [])
    return {**state, "previous_exam_path": previous_exam_path}

def check_exist_previous_exam(state: AgentState):
    """기출 문제 존재 여부 확인"""
    previous_exam_path = state.get("previous_exam_path", [])
    if not previous_exam_path or len(previous_exam_path) == 0:
        return "no exist"
    else:
        return "exist"

def analyze_previous_exam(state: AgentState):
    """기출 문제 분석하여 출제자 성향 파악"""
    try:
        previous_exam_path = state.get("previous_exam_path", [])
        personality = []
        
        for exam_file_path in previous_exam_path:
            try:
                # 파일 경로가 실제로 존재하는지 확인
                if not os.path.exists(exam_file_path):
                    logger.warning(f"기출문제 파일을 찾을 수 없음: {exam_file_path}")
                    continue
                
                loader = PDFPlumberLoader(exam_file_path)
                docs = loader.load()
                full_text = ""
                for doc in docs:
                    full_text += doc.page_content
                
                if full_text.strip():
                    result = llm.invoke(f"""다음 시험 문제를 참고하여 출제자의 성향을 분석해주세요. 
                                        이때 성향은 핵심 개념 위주, 지엽적인 설명 위주, 쉬운 문제 위주, 고난이도 문제 위주 등 다양한 성향이 있을 수 있으며 
                                        다음 시험 문제 출제자가 참고하기 좋도록 작성하여 주세요.
                        
                        시험 문제: {full_text[:2000]}""").content  # 너무 긴 텍스트 방지
                    
                    personality.append(result)
                    logger.info(f"기출문제 분석 완료: {exam_file_path}")
                else:
                    logger.warning(f"기출문제 내용이 비어있음: {exam_file_path}")
                    
            except Exception as file_error:
                logger.error(f"기출문제 파일 처리 실패 {exam_file_path}: {str(file_error)}")
                continue
        
        if not personality:
            logger.warning("분석된 기출문제가 없음. 기본 성향 사용")
            personality = ["균형 잡힌 출제 성향을 가진 출제자"]
        
        logger.info(f"출제자 성향 분석 완료: {len(personality)}개")
        return {**state, "personality": personality}
        
    except Exception as e:
        logger.error(f"기출문제 분석 실패: {str(e)}")
        return {**state, "personality": ["기본적인 출제 성향"], "error": f"기출문제 분석 실패: {str(e)}"}

def get_final_personality(state: AgentState):
    """여러 기출문제 성향을 종합하여 최종 성향 도출"""
    try:
        personality_list = state.get("personality", [])
        if not personality_list:
            final_personality = "균형 잡힌 문제를 출제하는 성향"
        elif len(personality_list) == 1:
            final_personality = personality_list[0]
        else:
            result = llm.invoke(f"""다음 성향 리스트는 같은 출제자의 여러 시험의 각 성향을 분석한 내용입니다. 
                                다음 내용을 참고하여 종합적인 출제자의 성향을 분석해주세요.
                                
                                성향 분석 결과들: {personality_list}""").content
            final_personality = result
        
        logger.info("최종 출제자 성향 도출 완료")
        return {**state, "final_personality": final_personality}
        
    except Exception as e:
        logger.error(f"최종 성향 도출 실패: {str(e)}")
        return {**state, "final_personality": "균형 잡힌 문제를 출제하는 성향"}

def select_exam_docs(state: AgentState):
    """시험 문제 출제용 문서 선택 (WebSocket에서 이미 설정됨)"""
    exam_docs_path = state.get("exam_docs_path", "")
    return {**state, "exam_docs_path": exam_docs_path}

def get_all_files(state: AgentState):
    """선택된 문서에서 모든 내용 추출"""
    try:
        exam_docs_path = state.get("exam_docs_path", "")
        if not exam_docs_path:
            return {**state, "exam_docs": "", "error": "시험 출제용 문서가 선택되지 않았습니다."}
        
        logger.info(f"시험 출제용 문서 로드: {exam_docs_path}")
        
        # get_all_docs 함수 사용하여 문서 내용 추출
        exam_docs = get_all_docs(exam_docs_path)
        
        if not exam_docs:
            return {**state, "exam_docs": "", "error": "문서 내용을 읽을 수 없습니다."}
        
        logger.info(f"문서 내용 로드 완료: {len(exam_docs)}자")
        return {**state, "exam_docs": exam_docs}
        
    except Exception as e:
        logger.error(f"문서 로드 실패: {str(e)}")
        return {**state, "exam_docs": "", "error": f"문서 로드 실패: {str(e)}"}

def get_concept_for_exam(state: AgentState):
    """출제용 개념 추출"""
    try:
        exam_docs = state.get("exam_docs", "")
        final_personality = state.get("final_personality", "균형 잡힌 출제 성향")
        
        if not exam_docs:
            return {**state, "concepts_for_exam": [], "error": "출제할 문서 내용이 없습니다."}
        
        # 문서가 너무 길면 분할
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=4000,
            chunk_overlap=500,
            length_function=len,
            is_separator_regex=False,
        )
        
        pdfs = text_splitter.create_documents([exam_docs])
        concepts_for_exam = []
        
        for i, pdf in enumerate(pdfs):
            logger.info(f"개념 추출 {i+1}/{len(pdfs)}")
            
            try:
                concept = llm.invoke(f"""당신은 {final_personality} 성격을 가진 시험 출제위원입니다.
                    
                    주어진 다음 내용을 보고 다음 내용에서 본인의 출제 성격에 맞춰 시험에 낼만한 내용 및 개념들을 이유와 함께 정리해주세요.
                    문제를 생성하는 것이 아닌 출제하고 싶은 내용을 정리하는 것입니다.
                    
                    내용: {pdf.page_content}""").content
                
                concepts_for_exam.append(concept)
                
            except Exception as chunk_error:
                logger.error(f"개념 추출 청크 {i+1} 실패: {str(chunk_error)}")
                concepts_for_exam.append(f"개념 추출 실패: {str(chunk_error)}")
        
        logger.info(f"출제 개념 추출 완료: {len(concepts_for_exam)}개")
        return {**state, "concepts_for_exam": concepts_for_exam}
        
    except Exception as e:
        logger.error(f"개념 추출 실패: {str(e)}")
        return {**state, "concepts_for_exam": [], "error": f"개념 추출 실패: {str(e)}"}

def refine_problems(state: AgentState):
    """추출된 개념을 바탕으로 시험 문제 생성"""
    try:
        concepts_for_exam = state.get("concepts_for_exam", [])
        final_personality = state.get("final_personality", "균형 잡힌 출제 성향")
        
        if not concepts_for_exam:
            return {**state, "problems": [], "error": "출제할 개념이 없습니다."}
        
        problems = []
        for i, concept in enumerate(concepts_for_exam):
            logger.info(f"문제 생성 {i+1}/{len(concepts_for_exam)}")
            
            try:
                problem = llm.invoke(f"""당신은 {final_personality} 성격을 가진 시험 문제 출제 위원입니다.
                    
                    제공된 내용은 시험에 내고 싶은 개념 및 내용과 이유입니다. 내용을 참고하여 시험 범위, 출제 이유, 필요한 학습 개념과 함께 시험 문제 5개를 생성해주세요.
                    각 내용은 결합되어도 됩니다. 예를 들어, A개념과 B개념 2가지가 적혀있는데 이 둘을 결합한 한 문제를 제작해주는 것은 괜찮습니다.
                    
                    생성하는 시험 문제의 난이도 비율(Easy:Medium:Hard)은 3:2:1로 생성해주세요.
                    
                    다른 설명과 같은 말은 하지 마시고, 시험 문제만 1~5번까지 5개 생성해주시면 됩니다.
                    
                    출제 개념: {concept}""").content
                
                problems.append(problem)
                
            except Exception as prob_error:
                logger.error(f"문제 생성 {i+1} 실패: {str(prob_error)}")
                problems.append(f"문제 생성 실패: {str(prob_error)}")
        
        logger.info(f"시험 문제 생성 완료: {len(problems)}개 세트")
        return {**state, "problems": problems}
        
    except Exception as e:
        logger.error(f"문제 생성 실패: {str(e)}")
        return {**state, "problems": [], "error": f"문제 생성 실패: {str(e)}"}

def save_exam(state: AgentState):
    """생성된 시험 문제를 파일로 저장"""
    try:
        problems = state.get("problems", [])
        user_id = state.get("user_id", "unknown")
        exam_docs_path = state.get("exam_docs_path", "unknown_document")
        
        if not problems:
            return {**state, "file_path": "", "error": "저장할 문제가 없습니다."}
        
        # 파일명 생성
        title = os.path.basename(exam_docs_path) if exam_docs_path else "exam"
        if title.endswith('.pdf'):
            title = title[:-4]
        
        # ✅ 수정 (통일된 경로)
        user_dir = f"storage/{user_id}/exam/"
        os.makedirs(user_dir, exist_ok=True)
        
        # 모든 문제를 하나의 파일로 합치기
        all_problems = "\n\n".join(problems)
        
        # 파일 저장
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        file_path = os.path.join(user_dir, f"{title}_{timestamp}.md")
        
        with open(file_path, "w", encoding="utf-8") as md_file:
            md_file.write(f"# {title} 시험 문제\n\n")
            md_file.write(f"**생성 일시**: {datetime.now().strftime('%Y년 %m월 %d일 %H시 %M분')}\n\n")
            md_file.write(all_problems)
        
        logger.info(f"시험 문제 파일 저장 완료: {file_path}")
        
        # 메시지에 결과 추가
        messages = state.get("messages", [])
        messages.append(AIMessage(content=all_problems))
        
        return {
            **state, 
            "messages": messages,
            "file_path": file_path,
            "result": all_problems
        }
        
    except Exception as e:
        logger.error(f"시험 문제 저장 실패: {str(e)}")
        return {**state, "file_path": "", "error": f"파일 저장 실패: {str(e)}"}