import os
import logging
import tempfile
import requests
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from gptpdf import parse_pdf

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
def process_pdf_upload(pdf_path: str, user_id: str, folder_name: str) -> dict:
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

    title = os.path.basename(pdf_path)
    user_dir = f"{user_id}/chroma/{folder_name}"
    os.makedirs(user_dir, exist_ok=True)

    # ✅ 파싱
    content, _ = parse_pdf(pdf_path, model="gpt-4.1-mini")

    # ✅ 청크 분할
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=3000, chunk_overlap=200)
    chunks = text_splitter.split_documents([Document(page_content=content)])

    for i, chunk in enumerate(chunks):
        chunk.metadata.update({
            "document_title": title,
            "chunk_id": i,
            "is_full_document": False,
            "document_type": "chunk",
            "user_id": user_id
        })

    full_doc = Document(page_content=content)
    full_doc.metadata.update({
        "document_title": title,
        "is_full_document": True,
        "document_type": "full",
        "user_id": user_id
    })

    # ✅ 저장
    embeddings = OpenAIEmbeddings()
    all_docs = chunks + [full_doc]

    if os.path.exists(user_dir) and os.listdir(user_dir):
        vs = Chroma(persist_directory=user_dir, embedding_function=embeddings)
        vs.add_documents(all_docs)
    else:
        Chroma.from_documents(documents=all_docs, embedding=embeddings, persist_directory=user_dir)

    return {
        "status": "success",
        "chunks_count": len(chunks),
        "filename": title
    }
