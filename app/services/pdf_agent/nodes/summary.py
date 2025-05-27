# app/services/pdf_agent/nodes/summary.py (ChromaDB 기반으로 완전 수정)

import json
import os
import logging
from datetime import datetime
from tqdm import tqdm
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from dotenv import load_dotenv

from app.services.pdf_agent.states import AgentState
from app.core.config import settings

load_dotenv()
llm = ChatOpenAI(model="gpt-4o-mini")
logger = logging.getLogger(__name__)

def start_point_of_summary(state: AgentState):
    print("요약 그래프 시작")
    return state

def get_related_pdf(state: AgentState):
    """ChromaDB에서 문서 검색하여 요약할 내용 가져오기"""
    try:
        user_id = state.get("user_id", "")
        pdf_path = state.get("pdf_path", "")
        
        if not user_id:
            return {**state, "pdf_content": "", "error": "사용자 ID가 없습니다."}
        
        # ChromaDB에서 해당 문서의 전체 내용 가져오기
        pdf_content = search_full_document_from_chromadb(user_id, pdf_path)
        
        if not pdf_content:
            return {**state, "pdf_content": "", "error": "ChromaDB에서 문서를 찾을 수 없습니다."}
        
        logger.info(f"ChromaDB에서 문서 로드 완료: {len(pdf_content)}자")
        return {**state, "pdf_content": pdf_content}
        
    except Exception as e:
        logger.error(f"ChromaDB 문서 로드 실패: {str(e)}")
        return {**state, "pdf_content": "", "error": f"문서 로드 실패: {str(e)}"}

def search_full_document_from_chromadb(user_id: str, pdf_path: str = "") -> str:
    """ChromaDB에서 전체 문서 내용 검색"""
    try:
        # ChromaDB 연결
        user_dir = f"{settings.CHROMADB_STORAGE_PATH}/{user_id}"
        if not os.path.exists(user_dir):
            logger.warning(f"ChromaDB 디렉토리가 없음: {user_dir}")
            return ""
        
        embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
        vectorstore = Chroma(persist_directory=user_dir, embedding_function=embeddings)
        
        # 전체 문서 가져오기
        if pdf_path:
            # 특정 파일의 전체 문서 검색
            filename = os.path.basename(pdf_path)
            # 파일명으로 필터링하여 is_full_document=True인 문서 찾기
            results = vectorstore.similarity_search(
                query=f"제목 파일명 {filename}",
                k=50,  # 많은 결과를 가져와서 필터링
                filter={"is_full_document": True}
            )
        else:
            # 모든 전체 문서 검색
            results = vectorstore.similarity_search(
                query="전체 문서 내용",
                k=10,
                filter={"is_full_document": True}
            )
        
        if not results:
            logger.warning("전체 문서를 찾을 수 없음. 일반 검색으로 대체")
            # 전체 문서가 없으면 일반 검색으로 많은 청크 가져오기
            results = vectorstore.similarity_search(
                query="문서 내용 요약",
                k=20  # 많은 청크를 가져와서 합치기
            )
        
        # 결과 합치기
        full_content = ""
        for doc in results:
            content = doc.page_content
            # "제목 : " 부분 제거
            if "제목 :" in content:
                content = content.split("내용 :", 1)[-1].strip()
            elif "내용 :" in content:
                content = content.split("내용 :", 1)[-1].strip()
            
            full_content += content + "\n\n"
        
        logger.info(f"ChromaDB에서 총 {len(results)}개 문서 조각 발견, 총 길이: {len(full_content)}")
        return full_content.strip()
        
    except Exception as e:
        logger.error(f"ChromaDB 검색 실패: {str(e)}")
        return ""

def pdf_parsing(state: AgentState):
    """ChromaDB에서 가져온 내용을 적절한 크기로 분할"""
    try:
        pdf_content = state.get("pdf_content", "")
        if not pdf_content:
            return {**state, "pdfs": [], "error": "분할할 내용이 없습니다."}
        
        content_length = len(pdf_content)
        logger.info(f"문서 내용 길이: {content_length}자")
        
        # 내용 길이에 따라 적절한 chunk_size 설정
        if content_length < 1000:
            # 짧은 내용은 분할하지 않음
            logger.info("내용이 짧아 분할하지 않음")
            return {**state, "pdfs": [pdf_content]}
        
        elif content_length < 5000:
            # 중간 길이: 3개 정도로 분할
            chunk_size = max(800, content_length // 3)
            chunk_overlap = min(100, chunk_size // 8)
        
        elif content_length < 15000:
            # 긴 내용: 5개 정도로 분할
            chunk_size = max(1500, content_length // 5)
            chunk_overlap = min(150, chunk_size // 10)
        
        else:
            # 매우 긴 내용: 3000자 단위로 분할
            chunk_size = 3000
            chunk_overlap = 200
        
        # chunk_overlap이 chunk_size보다 작은지 확인
        chunk_overlap = min(chunk_overlap, chunk_size - 1)
        
        logger.info(f"분할 설정: chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
        
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        
        pdfs = text_splitter.split_text(pdf_content)
        logger.info(f"내용 분할 완료: {len(pdfs)}개 청크")
        
        return {**state, "pdfs": pdfs}
        
    except Exception as e:
        logger.error(f"내용 분할 실패: {str(e)}")
        return {**state, "pdfs": [], "error": f"내용 분할 실패: {str(e)}"}

def summary_pdf(state: AgentState):
    """분할된 내용을 요약"""
    try:
        pdfs = state.get("pdfs", [])
        if not pdfs:
            return {**state, "result": "", "error": "요약할 내용이 없습니다."}
        
        logger.info(f"요약 시작: {len(pdfs)}개 청크")
        summaries = ""
        
        for i, pdf_chunk in enumerate(pdfs):
            logger.info(f"청크 {i+1}/{len(pdfs)} 요약 중... (길이: {len(pdf_chunk)}자)")
            
            try:
                result = llm.invoke(f"""다음 내용을 학습자료로 활용할 수 있도록 상세하게 요약해주세요. 
                                    마크다운 형식을 활용하여 구조화된 요약을 만들어주세요.
                                    주요 개념, 핵심 내용, 중요한 세부사항을 포함해서 요약해주세요.
                                    
                                    내용: {pdf_chunk}""").content
                
                summaries += f"## 섹션 {i+1}\n\n{result}\n\n"
                
            except Exception as chunk_error:
                logger.error(f"청크 {i+1} 요약 실패: {str(chunk_error)}")
                summaries += f"### 섹션 {i+1} 요약 실패\n오류: {str(chunk_error)}\n\n"
        
        logger.info("요약 완료")
        return {**state, "result": summaries}
        
    except Exception as e:
        logger.error(f"요약 실패: {str(e)}")
        return {**state, "result": "", "error": f"요약 실패: {str(e)}"}

def get_need_to_explain(state: AgentState):
    """배경지식 설명이 필요한 용어 추출"""
    try:
        result = state.get("result", "")
        if not result:
            return {**state, "need_to_explain": {}}
        
        example = '{"용어1":"설명이 필요한 이유","용어2":"설명이 필요한 이유"}'
        
        response = llm.invoke(f"""다음 요약 내용에서 학습자가 이해하기 어려울 수 있는 전문 용어나 개념들을 찾아서 
                              JSON 형식으로 정리해주세요. 다른 설명 없이 JSON만 출력해주세요.
                              
                              예시: {example}
                              
                              요약 내용: {result}""")
        
        try:
            need_to_explain = json.loads(response.content.strip())
            logger.info(f"설명 필요 용어 {len(need_to_explain)}개 추출")
            return {**state, "need_to_explain": need_to_explain}
        except json.JSONDecodeError:
            logger.warning("용어 추출 JSON 파싱 실패")
            return {**state, "need_to_explain": {}}
            
    except Exception as e:
        logger.error(f"용어 추출 실패: {str(e)}")
        return {**state, "need_to_explain": {}}

def explain(state: AgentState):
    """추출된 용어들에 대한 설명 생성"""
    try:
        need_to_explain = state.get("need_to_explain", {})
        if not need_to_explain:
            return {**state, "need_to_explain": {}}
        
        result_map = {}
        for term, reason in need_to_explain.items():
            try:
                question = f"{term}에 대해 간단하고 이해하기 쉽게 설명해주세요. ({reason})"
                explanation = llm.invoke(question).content
                result_map[term] = explanation
                logger.info(f"용어 설명 완료: {term}")
            except Exception as term_error:
                logger.error(f"용어 {term} 설명 실패: {str(term_error)}")
                result_map[term] = f"설명 생성 실패: {str(term_error)}"
        
        return {**state, "need_to_explain": result_map}
        
    except Exception as e:
        logger.error(f"용어 설명 실패: {str(e)}")
        return {**state, "need_to_explain": {}}

def add_explaination(state: AgentState):
    """요약 내용에 용어 설명 추가"""
    try:
        result = state.get("result", "")
        need_to_explain = state.get("need_to_explain", {})
        
        if not result:
            return {**state, "result": "요약 내용이 없습니다."}
        
        if not need_to_explain:
            logger.info("추가할 설명이 없음")
            return {**state, "result": result}
        
        # 용어 설명을 요약 끝에 추가
        final_result = result + "\n\n## 📚 용어 설명\n\n"
        
        for term, explanation in need_to_explain.items():
            final_result += f"### {term}\n{explanation}\n\n"
        
        logger.info("용어 설명 추가 완료")
        return {**state, "result": final_result}
        
    except Exception as e:
        logger.error(f"설명 추가 실패: {str(e)}")
        return state

def gen_sample_question(state: AgentState):
    """학습 확인용 문제 생성"""
    try:
        result = state.get("result", "")
        if not result:
            return state
        
        exam_prompt = """다음 학습 자료를 바탕으로 학습자가 내용을 잘 이해했는지 확인할 수 있는 
                        간단한 문제 3-5개를 만들어주세요. 주관식 문제로 만들어주세요.
                        
                        학습 자료: """ + result
        
        exam = llm.invoke(exam_prompt).content
        final_result = result + "\n\n## 📝 학습 확인 문제\n\n" + exam
        
        logger.info("학습 문제 생성 완료")
        return {**state, "result": final_result}
        
    except Exception as e:
        logger.error(f"문제 생성 실패: {str(e)}")
        return state

def save_file(state: AgentState):
    """요약 결과를 파일로 저장"""
    try:
        result = state.get("result", "")
        user_id = state.get("user_id", "unknown")
        pdf_path = state.get("pdf_path", "unknown_document")
        
        if not result:
            return {**state, "saved_path": "", "error": "저장할 내용이 없습니다."}
        
        # 파일명 생성
        filename = os.path.basename(pdf_path) if pdf_path else "document"
        if filename.endswith('.pdf'):
            filename = filename[:-4]  # .pdf 제거
        
        # 저장 디렉토리 생성
        user_dir = f"storage/{user_id}/summary"
        os.makedirs(user_dir, exist_ok=True)
        
        # 파일 저장
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        file_path = os.path.join(user_dir, f"{filename}_summary_{timestamp}.md")
        
        with open(file_path, "w", encoding="utf-8") as md_file:
            md_file.write(result)
        
        logger.info(f"요약 파일 저장 완료: {file_path}")
        return {**state, "saved_path": file_path}
        
    except Exception as e:
        logger.error(f"파일 저장 실패: {str(e)}")
        return {**state, "saved_path": "", "error": f"파일 저장 실패: {str(e)}"}