# app/services/pdf_agent/nodes/scheduler.py (ChromaDB 기반 수정)

import os
import json
import logging
from datetime import date, datetime
from dotenv import dotenv_values
from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

from app.services.pdf_agent.states import AgentState
from app.services.pdf_agent.tools import search_documents_for_qa

logger = logging.getLogger(__name__)
envs = dotenv_values(".env")
api_key = envs["OPENAI_API_KEY"]
llm = ChatOpenAI(model="gpt-4o-mini")

def start_point_of_schedule(state: AgentState):
    print("스케줄 그래프 시작")
    return state

def select_subjects(state: AgentState):
    """과목 선택 (WebSocket에서 이미 설정됨)"""
    subjects = state.get("subjects", [])
    if not subjects:
        # 기본값 설정
        subjects = ["과목1", "과목2"]
    
    return {**state, "subject_index": 0, "subjects": subjects}

def select_importance(state: AgentState):
    """중요도 선택 (WebSocket에서 이미 설정됨)"""
    importance = state.get("importance", {})
    return {**state, "importance": importance}

def select_deadlines(state: AgentState):
    """마감일 선택 (WebSocket에서 이미 설정됨)"""
    deadlines = state.get("deadlines", {})
    return {**state, "deadlines": deadlines}

def get_all_document(state: AgentState):
    """ChromaDB에서 선택된 파일들의 내용 가져오기"""
    try:
        selected_files = state.get("selected_files", [])
        user_id = state.get("user_id", "")
        
        if not selected_files or not user_id:
            return {**state, "docs": [], "error": "선택된 파일이나 사용자 ID가 없습니다."}
        
        docs = []
        for file_path in selected_files:
            try:
                # 파일명으로 ChromaDB에서 검색
                filename = os.path.basename(file_path)
                
                # ChromaDB에서 해당 파일의 목차 정보 검색
                search_results = search_documents_for_qa(
                    user_id=user_id, 
                    query=f"목차 인덱스 {filename}",
                    k=10
                )
                
                # 검색 결과에서 목차 정보 추출
                file_content = ""
                for doc, score in search_results:
                    content = doc.page_content
                    # 목차나 인덱스 관련 내용 필터링
                    if "목차" in content or "인덱스" in content or "차례" in content:
                        file_content += content + "\n"
                
                if not file_content:
                    # 목차가 없으면 일반 내용으로 대체
                    general_results = search_documents_for_qa(
                        user_id=user_id,
                        query=f"{filename} 내용 개요",
                        k=5
                    )
                    for doc, score in general_results:
                        file_content += doc.page_content[:500] + "\n"  # 일부만 가져오기
                
                docs.append(file_content)
                logger.info(f"문서 내용 추출 완료: {filename}")
                
            except Exception as file_error:
                logger.error(f"파일 처리 실패 {file_path}: {str(file_error)}")
                docs.append(f"파일 처리 실패: {file_path}")
        
        logger.info(f"총 {len(docs)}개 문서 처리 완료")
        return {**state, "docs": docs}
        
    except Exception as e:
        logger.error(f"문서 수집 실패: {str(e)}")
        return {**state, "docs": [], "error": f"문서 수집 실패: {str(e)}"}

def define_final_index(state: AgentState):
    """각 과목별 최종 목차 생성"""
    try:
        docs = state.get("docs", [])
        subjects = state.get("subjects", [])
        
        if not docs:
            return {**state, "final_index": [], "error": "처리할 문서가 없습니다."}
        
        final_index = []
        
        for i, (doc, subject) in enumerate(zip(docs, subjects)):
            logger.info(f"과목 {subject} 목차 생성 중...")
            
            try:
                if doc.strip():
                    index_result = llm.invoke(f"""다음 내용은 '{subject}' 과목의 학습 자료입니다.
                        이 내용을 바탕으로 학습 계획을 세울 수 있도록 체계적인 목차를 생성해주세요.
                        주요 단원, 핵심 개념, 학습해야 할 세부 내용을 포함해서 구조화된 목차를 만들어주세요.
                        
                        과목명: {subject}
                        학습 자료 내용: {doc[:2000]}""").content  # 너무 긴 내용 방지
                else:
                    index_result = f"{subject} - 기본 학습 목차\n1. 기초 개념\n2. 주요 이론\n3. 응용 및 실습"
                
                final_index.append(index_result)
                logger.info(f"과목 {subject} 목차 생성 완료")
                
            except Exception as subject_error:
                logger.error(f"과목 {subject} 목차 생성 실패: {str(subject_error)}")
                final_index.append(f"{subject} - 목차 생성 실패: {str(subject_error)}")
        
        logger.info(f"전체 목차 생성 완료: {len(final_index)}개 과목")
        return {**state, "final_index": final_index}
        
    except Exception as e:
        logger.error(f"목차 생성 실패: {str(e)}")
        return {**state, "final_index": [], "error": f"목차 생성 실패: {str(e)}"}

def check_sub_count(state: AgentState):
    """과목 처리 완료 여부 확인"""
    subject_index = state.get("subject_index", 0)
    subjects = state.get("subjects", [])
    
    if subject_index >= len(subjects):
        return "completion"
    else:
        return "continue"

def make_plans(state: AgentState):
    """학습 계획 생성"""
    try:
        subjects = state.get("subjects", [])
        final_index = state.get("final_index", [])
        importance = state.get("importance", {})
        deadlines = state.get("deadlines", {})
        today = date.today()
        
        if not subjects or not final_index:
            return {**state, "schedule": {}, "error": "학습 계획 생성에 필요한 정보가 부족합니다."}
        
        # 과목별 정보 구성
        total_subjects = {}
        for subject, index in zip(subjects, final_index):
            subject_importance = importance.get(subject, 3)  # 기본값 3
            subject_deadline = deadlines.get(subject, str(today))  # 기본값 오늘
            
            total_subjects[subject] = {
                "목차": index,
                "중요도": subject_importance,
                "마감일": subject_deadline
            }
        
        # 스케줄 생성 예시 형식
        example = {
            "2025-05-27": {
                "과목1": {
                    "학습할 범위": "1장 기초개념 학습",
                    "예상 학습 시간": "2시간",
                    "학습 방법": "이론 정리 및 개념 이해"
                },
                "과목2": {
                    "학습할 범위": "기본 이론 복습",
                    "예상 학습 시간": "1시간",
                    "학습 방법": "문제 풀이"
                }
            }
        }
        
        schedule_prompt = f"""다음 제공된 과목 정보를 바탕으로 효율적인 학습 계획표를 작성해주세요.
        
        고려사항:
        1. 각 과목의 목차 범위와 양
        2. 각 과목의 중요도 (1-5점)
        3. 오늘 날짜({today})부터 각 과목의 마감일까지의 기간
        4. 하루 최대 가용시간 9시간을 효율적으로 활용
        
        학습 계획은 구체적으로 어떤 내용을 어떻게 공부할지 포함해야 하며,
        시험 전날에는 해당 과목의 비중을 높여주세요.
        
        다음 JSON 구조로만 출력해주세요 (다른 설명 없이):
        {json.dumps(example, ensure_ascii=False, indent=2)}
        
        과목 정보:
        {json.dumps(total_subjects, ensure_ascii=False, indent=2)}"""
        
        logger.info("학습 계획 생성 중...")
        result = llm.invoke(schedule_prompt).content
        
        # JSON 파싱 시도
        try:
            # JSON 부분만 추출
            if "```json" in result:
                result = result.split("```json")[1].split("```")[0]
            elif "```" in result:
                result = result.split("```")[1].split("```")[0]
            
            schedule_data = json.loads(result)
            logger.info("학습 계획 생성 완료")
            return {**state, "schedule": schedule_data}
            
        except json.JSONDecodeError:
            logger.warning("JSON 파싱 실패, 텍스트 형태로 저장")
            return {**state, "schedule": {"raw_plan": result}}
        
    except Exception as e:
        logger.error(f"학습 계획 생성 실패: {str(e)}")
        return {**state, "schedule": {}, "error": f"학습 계획 생성 실패: {str(e)}"}

def save_plan(state: AgentState):
    """생성된 학습 계획을 파일로 저장"""
    try:
        schedule = state.get("schedule", {})
        user_id = state.get("user_id", "unknown")
        
        if not schedule:
            return {**state, "schedule_file_path": "", "error": "저장할 계획이 없습니다."}
        
        # 저장 디렉토리 생성
        user_dir = f"storage/{user_id}/schedule"
        os.makedirs(user_dir, exist_ok=True)
        
        # 파일명 생성
        existing_files = len([f for f in os.listdir(user_dir) if f.startswith("schedule_")])
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"schedule_{existing_files + 1}_{timestamp}.json"
        file_path = os.path.join(user_dir, filename)
        
        # JSON 파일로 저장
        with open(file_path, "w", encoding="utf-8") as json_file:
            json.dump(schedule, json_file, ensure_ascii=False, indent=4)
        
        logger.info(f"학습 계획 저장 완료: {file_path}")
        
        # 메시지에 결과 추가
        messages = state.get("messages", [])
        schedule_text = json.dumps(schedule, ensure_ascii=False, indent=2)
        messages.append(AIMessage(content=f"학습 계획이 생성되었습니다:\n\n```json\n{schedule_text}\n```"))
        
        return {
            **state,
            "messages": messages,
            "schedule_file_path": file_path,
            "schedule": schedule  # ✅ 즉시 전송용 JSON 포함
        }
        
    except Exception as e:
        logger.error(f"학습 계획 저장 실패: {str(e)}")
        return {**state, "schedule_file_path": "", "error": f"파일 저장 실패: {str(e)}"}