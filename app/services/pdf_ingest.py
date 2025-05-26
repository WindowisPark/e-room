import os
import logging
import tempfile
import requests
from langchain_community.document_loaders import PDFPlumberLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from gptpdf import parse_pdf
from langchain_openai import ChatOpenAI
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
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", ""),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        region_name=os.getenv("AWS_REGION", "ap-northeast-2")
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
    
def process_pdf_upload(pdf_path: str, user_id: str) -> dict:
    """
    S3 또는 로컬 PDF 경로를 받아 문서를 파싱하고 ChromaDB에 저장

    Args:
        pdf_path: 로컬 경로 또는 S3 URL
        user_id: 사용자 ID
        folder_name: 저장 폴더명

    Returns:
        처리 결과 요약
    """
    # ✅ S3 URL이면 다운로드
    if pdf_path.startswith("http://") or pdf_path.startswith("https://"):
        logger.info(f"URL 기반 PDF 감지됨, 임시 파일로 다운로드 중: {pdf_path}")
        pdf_path = download_s3_pdf_tempfile(pdf_path)

    docs_explanation= input("이것은 무슨 자료인가요? (Skip : Enter)") # 더 잘 검색하기 위함 사용자한테 뭔지 적어달라고좀 해줘잉
    title = os.path.basename(pdf_path)
    user_dir = f"{user_id}/chroma/"
    os.makedirs(user_dir, exist_ok=True)
    llm = ChatOpenAI(model = "gpt-4.1-mini")
    # ✅ 파싱
    loader = PDFPlumberLoader(pdf_path) # <- 수정
    docs = loader.load() # <- 수정

    # ✅ 청크 분할
    full_text = ""
    for doc in docs:
        full_text+= "\n\n"+doc.page_content
    
    title = llm.invoke(f"""다음 내용을 설명할 수 있는 제목만 상세하게 작성해주세요. 
                       다른 부가적 설명없이 제가 바로 문서 제목으로 사용할 수 있도록 제목만 자세하게 작성해주시면 됩니다. 
                       다시 한 번 말하지만, 제목만 말해주세요. 제목만.
                       \n내용:{full_text}""").content
    title = docs_explanation+"\n"+title
    full_document = Document(page_content="제목 : "+title+"\n 내용 : "+full_text)
    for doc in docs: 
        # 기존 메타데이터 유지하면서 추가 정보 기록
        doc = Document(page_content="제목 : "+title+"\n 내용 : "+doc.page_content)
        doc.metadata.update({
            "source":title,
            "is_full_document": False,
        })

    if full_document:
        full_document.metadata.update({
            "source":title,
            "is_full_document": True,
        })
    indices = llm.invoke(f"다른 대답 없이 다음 주어진 내용 전체를 포함하는 목차만 생성해주세요. {full_text}").content
    indice_document = Document(page_content="제목 : "+title+"\n 목차 : "+indices)
    if indice_document:
        indice_document.metadata.update({
            "source":title,
            "indices" : True,
        })
    
    # ✅ 저장
    embeddings = OpenAIEmbeddings()
    all_docs = docs + ([full_document] if full_document else []) + ([indice_document] if indice_document else [])

    if os.path.exists(user_dir) and os.listdir(user_dir):
        vs = Chroma(persist_directory=user_dir, embedding_function=embeddings)
        vs.add_documents(all_docs)
    else:
        vs = Chroma.from_documents(documents=all_docs, embedding=embeddings, persist_directory=user_dir)

    return {
        "status": "success",
        "filename": title
    }