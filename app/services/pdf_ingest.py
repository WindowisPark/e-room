import os
import logging
import tempfile
import requests
from langchain_community.document_loaders import PDFPlumberLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_openai import ChatOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)

def download_s3_pdf_tempfile(s3_url: str) -> str:
    """
    S3 URL을 서명된 URL로 변환해 다운로드
    """
    import boto3
    from urllib.parse import urlparse

    # URL 파싱
    parsed = urlparse(s3_url)
    bucket = parsed.netloc.split('.')[0]
    key = parsed.path.lstrip('/')

    # 서명된 URL 생성
    s3 = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY,
        aws_secret_access_key=settings.AWS_SECRET_KEY,
        region_name=settings.AWS_REGION
    )

    try:
        signed_url = s3.generate_presigned_url(
            ClientMethod='get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=60  # 60초 동안 유효
        )

        response = requests.get(signed_url)
        if response.status_code != 200:
            raise ValueError(f"Signed URL 다운로드 실패: {signed_url}")

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            tmp_file.write(response.content)
            return tmp_file.name

    except Exception as e:
        raise ValueError(f"S3 Signed URL 생성 실패 또는 다운로드 실패: {str(e)}")
    
def process_pdf_upload(pdf_path: str, user_id: str, folder_name: str = "default", docs_explanation: str = "") -> dict:
    """
    S3 또는 로컬 PDF 경로를 받아 문서를 파싱하고 ChromaDB에 저장

    Args:
        pdf_path: 로컬 경로 또는 S3 URL
        user_id: 사용자 ID
        folder_name: 저장 폴더명
        docs_explanation: 문서 설명 (옵션)

    Returns:
        처리 결과 요약
    """
    try:
        # ✅ S3 URL이면 다운로드
        if pdf_path.startswith("http://") or pdf_path.startswith("https://"):
            logger.info(f"URL 기반 PDF 감지됨, 임시 파일로 다운로드 중: {pdf_path}")
            pdf_path = download_s3_pdf_tempfile(pdf_path)

        # 파일명 추출
        original_filename = os.path.basename(pdf_path)
        
        # ChromaDB 저장 경로 설정
        user_dir = f"{settings.CHROMADB_STORAGE_PATH}/{user_id}"
        os.makedirs(user_dir, exist_ok=True)
        
        # LLM 초기화
        llm = ChatOpenAI(
            model="gpt-4o-mini", 
            api_key=settings.AI_API_KEY,
            temperature=0
        )
        
        # ✅ PDF 파싱
        loader = PDFPlumberLoader(pdf_path)
        docs = loader.load()

        # ✅ 전체 텍스트 추출
        full_text = ""
        for doc in docs:
            full_text += "\n\n" + doc.page_content
        
        # ✅ LLM으로 제목 생성
        title_prompt = f"""다음 내용을 설명할 수 있는 제목만 상세하게 작성해주세요. 
                       다른 부가적 설명없이 제가 바로 문서 제목으로 사용할 수 있도록 제목만 자세하게 작성해주시면 됩니다. 
                       다시 한 번 말하지만, 제목만 말해주세요. 제목만.
                       \n내용:{full_text[:2000]}"""  # 토큰 제한 고려
        
        generated_title = llm.invoke(title_prompt).content.strip()
        
        # 최종 제목 구성
        if docs_explanation:
            title = f"{docs_explanation}\n{generated_title}"
        else:
            title = generated_title
        
        # ✅ 문서 객체 생성
        # 1. 전체 문서
        full_document = Document(
            page_content=f"제목 : {title}\n 내용 : {full_text}",
            metadata={
                "source": title,
                "is_full_document": True,
                "original_filename": original_filename,
                "folder": folder_name
            }
        )
        
        # 2. 페이지별 문서들
        page_documents = []
        for i, doc in enumerate(docs):
            page_doc = Document(
                page_content=f"제목 : {title}\n 내용 : {doc.page_content}",
                metadata={
                    "source": title,
                    "is_full_document": False,
                    "page_number": i + 1,
                    "original_filename": original_filename,
                    "folder": folder_name
                }
            )
            page_documents.append(page_doc)
        
        # 3. 목차 문서
        indices_prompt = f"다른 대답 없이 다음 주어진 내용 전체를 포함하는 목차만 생성해주세요. {full_text[:2000]}"
        indices = llm.invoke(indices_prompt).content.strip()
        
        indice_document = Document(
            page_content=f"제목 : {title}\n 목차 : {indices}",
            metadata={
                "source": title,
                "is_indices": True,
                "original_filename": original_filename,
                "folder": folder_name
            }
        )
        
        # ✅ ChromaDB에 저장
        embeddings = OpenAIEmbeddings(api_key=settings.AI_API_KEY)
        all_docs = page_documents + [full_document, indice_document]
        
        # 기존 ChromaDB 확인 및 저장
        if os.path.exists(user_dir) and os.listdir(user_dir):
            # 기존 벡터스토어에 추가
            vectorstore = Chroma(persist_directory=user_dir, embedding_function=embeddings)
            vectorstore.add_documents(all_docs)
        else:
            # 새로 생성
            vectorstore = Chroma.from_documents(
                documents=all_docs, 
                embedding=embeddings, 
                persist_directory=user_dir
            )
        
        # 임시 파일 정리 (S3에서 다운로드한 경우)
        if pdf_path.startswith("/tmp/") or pdf_path.startswith("/var/folders/"):
            try:
                os.unlink(pdf_path)
                logger.info(f"임시 파일 삭제 완료: {pdf_path}")
            except Exception as e:
                logger.warning(f"임시 파일 삭제 실패: {e}")
        
        logger.info(f"PDF 파싱 및 ChromaDB 저장 완료: {original_filename}")
        
        return {
            "status": "success",
            "filename": original_filename,
            "generated_title": generated_title,
            "total_pages": len(docs),
            "total_documents": len(all_docs),
            "folder": folder_name
        }
        
    except Exception as e:
        logger.error(f"PDF 처리 중 오류 발생: {str(e)}", exc_info=True)
        
        # 임시 파일 정리 (오류 시에도)
        if 'pdf_path' in locals() and (pdf_path.startswith("/tmp/") or pdf_path.startswith("/var/folders/")):
            try:
                os.unlink(pdf_path)
            except:
                pass
        
        return {
            "status": "error",
            "message": str(e),
            "filename": original_filename if 'original_filename' in locals() else "unknown"
        }