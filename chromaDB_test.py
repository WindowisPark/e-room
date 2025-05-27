# ChromaDB 상태 확인 디버깅 스크립트
import os
from pathlib import Path
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from dotenv import load_dotenv
load_dotenv()
def check_chromadb_status(user_id: str = "2"):
    """ChromaDB 상태 확인"""
    print(f"🔍 사용자 {user_id}의 ChromaDB 상태 확인")
    print("=" * 50)
    
    # 1. ChromaDB 디렉토리 확인
    chromadb_path = f"./storage/chromadb/{user_id}"
    print(f"📁 ChromaDB 경로: {chromadb_path}")
    
    if os.path.exists(chromadb_path):
        print("✅ ChromaDB 디렉토리 존재")
        
        # 디렉토리 내용 확인
        files = list(Path(chromadb_path).rglob("*"))
        print(f"📄 총 {len(files)}개 파일 발견:")
        for file in files[:10]:  # 최대 10개만 표시
            print(f"  - {file}")
        if len(files) > 10:
            print(f"  ... 그 외 {len(files) - 10}개")
    else:
        print("❌ ChromaDB 디렉토리 없음")
        return False
    
    # 2. ChromaDB 연결 테스트
    try:
        
        print("\n🔗 ChromaDB 연결 테스트...")
        embeddings = OpenAIEmbeddings(api_key=os.getenv("OPENAI_API_KEY"))
        vectorstore = Chroma(
            persist_directory=chromadb_path, 
            embedding_function=embeddings
        )
        
        # 3. 저장된 문서 수 확인
        collection = vectorstore._collection
        count = collection.count()
        print(f"📊 저장된 문서 수: {count}")
        
        if count > 0:
            # 문서 샘플 확인
            sample_docs = collection.peek(limit=3)
            print(f"📄 문서 샘플:")
            for i, doc in enumerate(sample_docs['documents']):
                print(f"  {i+1}. {doc[:100]}...")
                
            # 메타데이터 확인
            if sample_docs['metadatas']:
                print(f"🏷️ 메타데이터 샘플:")
                for i, meta in enumerate(sample_docs['metadatas'][:3]):
                    print(f"  {i+1}. {meta}")
        
        # 4. 검색 테스트
        print(f"\n🔍 검색 테스트...")
        test_query = "정보보호"
        results = vectorstore.similarity_search_with_score(test_query, k=3)
        print(f"검색어 '{test_query}'에 대한 결과: {len(results)}개")
        
        for i, (doc, score) in enumerate(results):
            print(f"  {i+1}. Score: {score:.4f}")
            print(f"     Content: {doc.page_content[:100]}...")
            print(f"     Metadata: {doc.metadata}")
        
        return True
        
    except Exception as e:
        print(f"❌ ChromaDB 연결 오류: {str(e)}")
        return False

def check_pdf_ingest_process():
    """PDF 인제스트 과정 확인"""
    print(f"\n📥 PDF 인제스트 과정 확인")
    print("=" * 50)
    
    # 최근 업로드된 파일 확인
    storage_path = "./storage"
    if os.path.exists(storage_path):
        print(f"✅ 스토리지 디렉토리 존재: {storage_path}")
        
        # 사용자별 디렉토리 확인
        for user_dir in Path(storage_path).iterdir():
            if user_dir.is_dir():
                print(f"👤 사용자: {user_dir.name}")
                
                # ChromaDB와 파일 디렉토리 확인
                chromadb_dir = user_dir / "chromadb"
                files_dirs = [d for d in user_dir.iterdir() if d.is_dir() and d.name != "chromadb"]
                
                if chromadb_dir.exists():
                    chromadb_files = list(chromadb_dir.rglob("*"))
                    print(f"  📊 ChromaDB 파일: {len(chromadb_files)}개")
                else:
                    print(f"  ❌ ChromaDB 없음")
                
                for files_dir in files_dirs:
                    file_count = len(list(files_dir.rglob("*.md")))
                    print(f"  📁 {files_dir.name}: {file_count}개 결과 파일")
    else:
        print(f"❌ 스토리지 디렉토리 없음: {storage_path}")

def manual_chromadb_test():
    """수동 ChromaDB 테스트"""
    print(f"\n🧪 수동 ChromaDB 테스트")
    print("=" * 50)
    
    try:
        from langchain_core.documents import Document
        
        # 테스트 문서 생성
        test_docs = [
            Document(
                page_content="정보보호의 기본 원칙은 기밀성, 무결성, 가용성입니다.",
                metadata={"source": "test_doc", "type": "manual_test"}
            ),
            Document(
                page_content="암호화는 데이터를 보호하는 중요한 기술입니다.",
                metadata={"source": "test_doc", "type": "manual_test"}
            )
        ]
        
        # ChromaDB에 저장
        embeddings = OpenAIEmbeddings()
        test_path = "./storage/chromadb/test"
        
        # 기존 테스트 디렉토리 제거
        import shutil
        if os.path.exists(test_path):
            shutil.rmtree(test_path)
        
        vectorstore = Chroma.from_documents(
            documents=test_docs,
            embedding=embeddings,
            persist_directory=test_path
        )
        
        print("✅ 테스트 문서 저장 완료")
        
        # 검색 테스트
        results = vectorstore.similarity_search("정보보호", k=2)
        print(f"🔍 검색 결과: {len(results)}개")
        
        for i, doc in enumerate(results):
            print(f"  {i+1}. {doc.page_content}")
        
        # 정리
        shutil.rmtree(test_path)
        print("🧹 테스트 디렉토리 정리 완료")
        
        return True
        
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        return False

if __name__ == "__main__":
    print("🔧 ChromaDB 진단 도구")
    print("=" * 60)
    
    # 1. 기본 상태 확인
    check_chromadb_status()
    
    # 2. 스토리지 구조 확인
    check_pdf_ingest_process()
    
    # 3. 수동 테스트
    manual_chromadb_test()
    
    print("\n✅ 진단 완료")