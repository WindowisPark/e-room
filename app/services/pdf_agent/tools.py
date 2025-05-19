from langchain_core.messages import SystemMessage
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import dotenv_values


def get_initial_state():
    return {
        "messages": [SystemMessage(content="""당신은 학생들을 가르치는 것으로 국내 0.1%의 명성을 가진 교육자입니다.\n
                                   다음 사용자의 요청에 따라 작업을 수행해주시면 됩니다. 사용자의 요청은 총 4가지로 이루어져 있습니다.\n
                                   1. 질의 응답, 2. 학습 자료 요약, 3. 시험 문제 생성 , 4. 학습 계획 세우기입니다.\n
                                   특히 질의 응답의 경우, 자료에 근거하여 답변해주시되, 질문에 답하기 위한 좋은 자료가 존재하지 않다면, 당신이 아닌 지식으로 답변해주시면 됩니다.\n

                                   사용자의 요청에 친절하고 자세한 설명으로 국내 0.1% 명성에 맞게 학습자의 이해를 도와주시면 됩니다.
                                   """)],
        "user_id":"1",
        "purpose": "",
        "full_document" : True,
        "pdf_content" : "",
        "pdfs": [],
        "pdf_step": 0,
        "summaries": "",
        "result": "",
        "explain_step": 0,
        "need_to_explain": {},
        "subject_index": 0,
        "final_index": [],
        "personality": [],
        "final_personality": ""
    }

def search_documents_for_qa(user_id: str, query: str, folder: str,k: int = 2):
    """
    질문을 위해 사용자의 ChromaDB에서 쿼리와 관련된 문서를 검색하는 함수

    Args:
        user_id: 사용자 ID
        query: 검색 쿼리
        k: 반환할 결과 수

    Returns:
        검색 결과 문서 리스트
    """
    print("1")
    # 환경 변수 로드
    envs = dotenv_values(".env")
    api_key = envs["OPENAI_API_KEY"]
    # 사용자 ChromaDB 경로
    user_dir = f"{user_id}/chroma/{folder}"

    # 임베딩 모델 초기화
    embeddings = OpenAIEmbeddings(api_key=api_key)

    # ChromaDB 로드
    vectorstore = Chroma(persist_directory=user_dir, embedding_function=embeddings)

    # 유사도 검색 실행
    results = vectorstore.similarity_search_with_score(query, k=2,filter={"is_full_document": False})
    print(results)
    filtered_docs = [doc for doc, score in results if score >= 0.34]


    return results

# 사용 예시
if __name__ == "__main__":
    user_id = "1"
    query = "세종대학교에서 제안한 에이전트가 뭐야?"

    search_results = search_documents_for_qa(user_id, query)

    # 검색 결과 출력
    for i, doc in enumerate(search_results):
        print(f"결과 {i+1}:")
        print(f"내용: {doc.page_content[:200]}...")  # 내용 일부만 출력
        print(f"메타데이터: {doc.metadata}")
        print("-" * 50)

def search_documents_for_summary(user_id: str, folder: str, query: str, k: int = 2):
    """
    요약을 위해 사용자의 ChromaDB에서 쿼리와 관련된 문서를 검색하는 함수

    Args:
        user_id: 사용자 ID
        query: 검색 쿼리
        k: 반환할 결과 수

    Returns:
        검색 결과 문서 리스트
    """
    print("1")
    # 환경 변수 로드
    envs = dotenv_values(".env")
    api_key = envs["OPENAI_API_KEY"]
    # 사용자 ChromaDB 경로
    user_dir = f"{user_id}/chroma/{folder}"

    # 임베딩 모델 초기화
    embeddings = OpenAIEmbeddings(api_key=api_key)

    # ChromaDB 로드
    vectorstore = Chroma(persist_directory=user_dir, embedding_function=embeddings)

    # 유사도 검색 실행
    results = vectorstore.similarity_search(query, k=1,filter={"is_full_document": True})


    return results


def search_documents_for_scheduler(user_id: str,folder:str, k: int = 2):
    """
    요약을 위해 사용자의 ChromaDB에서 쿼리와 관련된 문서를 검색하는 함수

    Args:
        user_id: 사용자 ID
        query: 검색 쿼리
        k: 반환할 결과 수

    Returns:
        검색 결과 문서 리스트
    """
    print("1")
     # 환경 변수 로드
    envs = dotenv_values(".env")
    api_key = envs["OPENAI_API_KEY"]
    # 사용자 ChromaDB 경로
    user_dir = f"{user_id}/chroma/{folder}"

    # 임베딩 모델 초기화
    embeddings = OpenAIEmbeddings(api_key=api_key)
    vectorstore = Chroma(persist_directory=user_dir, embedding_function=embeddings)

    # 메타데이터 필터링을 통해 문서 검색
    documents = vectorstore.get(
        where={"indices": True}
    )

    return documents

def search_documents_for_exam(user_id: str,folder:str):
    """
    요약을 위해 사용자의 ChromaDB에서 쿼리와 관련된 문서를 검색하는 함수

    Args:
        user_id: 사용자 ID
        query: 검색 쿼리
        k: 반환할 결과 수

    Returns:
        검색 결과 문서 리스트
    """
    print("1")
     # 환경 변수 로드
    envs = dotenv_values(".env")
    api_key = envs["OPENAI_API_KEY"]
    # 사용자 ChromaDB 경로
    user_dir = f"{user_id}/chroma/{folder}"

    # 임베딩 모델 초기화
    embeddings = OpenAIEmbeddings(api_key=api_key)
    vectorstore = Chroma(persist_directory=user_dir, embedding_function=embeddings)

    # 메타데이터 필터링을 통해 문서 검색
    documents = vectorstore.get(
        where={"is_full_document": True}
    )

    return documents