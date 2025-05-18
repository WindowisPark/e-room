# app/workers/worker.py
"""
PDF 작업 워커 프로세스
실행: python -m app.workers.worker
"""

import os
import sys
import time
import logging
import redis
from redis import Redis
from rq import Worker, Queue, Connection
from rq.job import Job
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import SessionLocal
# 제일 중요한 부분: 모든 모델을 먼저 임포트하여 SQLAlchemy가 관계를 설정할 수 있도록 함
from app.db.base_models import *  # 이 부분이 중요합니다!
from app.services.pdf_agent.processor import PDFProcessor
from app.services.notification_service import send_notification

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('worker')

# ✅ Redis 연결 설정 (settings.REDIS_URL 사용)
conn = Redis.from_url(settings.REDIS_URL)

# 작업 처리 전 작업
def before_job_hook(job, *args, **kwargs):
    logger.info(f"작업 시작: {job.id}, 큐: {job.origin}, 함수: {job.func_name}")
    job.meta['status'] = 'processing'
    job.meta['progress'] = 0
    job.meta['started_at'] = time.time()
    job.save_meta()

# 작업 처리 후 작업
def after_job_hook(job, connection, result, *args, **kwargs):
    if job.is_failed:
        logger.error(f"작업 실패: {job.id}, 오류: {job.exc_info}")
        job.meta['status'] = 'failed'
        job.meta['error'] = job.exc_info
    else:
        logger.info(f"작업 완료: {job.id}, 결과: {result}")
        job.meta['status'] = 'completed'
        job.meta['result'] = result

    job.meta['completed_at'] = time.time()
    job.meta['duration'] = job.meta.get('completed_at', 0) - job.meta.get('started_at', 0)
    job.save_meta()

    try:
        if not job.is_failed and 'user_id' in job.kwargs:
            user_id = job.kwargs.get('user_id')
            with SessionLocal() as db:
                send_notification(
                    db=db,
                    user_id=user_id,
                    type="system",
                    message=f"작업이 완료되었습니다: {job.description}",
                    link=f"/tasks/{job.id}/result"
                )
    except Exception as e:
        logger.error(f"알림 전송 실패: {str(e)}")

# 작업 실패 처리
def handle_job_failure(job, *args, **kwargs):
    logger.error(f"작업 실패 처리: {job.id}, 오류: {job.exc_info}")
    job.meta['status'] = 'failed'
    job.meta['error'] = job.exc_info
    job.meta['failed_at'] = time.time()
    job.save_meta()

    try:
        if 'user_id' in job.kwargs:
            user_id = job.kwargs.get('user_id')
            with SessionLocal() as db:
                send_notification(
                    db=db,
                    user_id=user_id,
                    type="system",
                    message=f"작업 처리 중 오류가 발생했습니다: {job.description}",
                    link=f"/tasks/{job.id}/result"
                )
    except Exception as e:
        logger.error(f"실패 알림 전송 오류: {str(e)}")

# 사용자 정의 Job 클래스
class CustomJob(Job):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def perform(self):
        before_job_hook(self)
        try:
            result = super().perform()
            after_job_hook(self, self.connection, result)
            return result
        except Exception:
            handle_job_failure(self)
            raise

# PDF 문서 작업 처리 함수
import asyncio

def wrapper_process_and_embed_document(document_id=None, user_id=None, **kwargs):
    """
    PDF 문서 처리 및 임베딩 생성 작업 래퍼 함수
    
    Args:
        document_id: 문서 ID (필수)
        user_id: 사용자 ID (필수)
        kwargs: 추가 인자들
    """
    from sqlalchemy.orm import Session
    import traceback
    from app.db.session import SessionLocal
    
    # 세션 생성 (worker에서는 항상 새 세션 생성)
    db = SessionLocal()
    
    try:
        logger.info(f"Processing document ID: {document_id}, user_id: {user_id}, kwargs={kwargs}")
        
        # 모델 초기화 명시적 임포트
        import app.models.user
        import app.models.tag
        import app.models.task
        import app.models.team
        
        # document_id 체크
        if document_id is None:
            return {"success": False, "error": "문서 ID가 제공되지 않았습니다"}
            
        # user_id 체크
        if user_id is None:
            return {"success": False, "error": "사용자 ID가 제공되지 않았습니다"}
        
        # 정수 변환 시도
        try:
            document_id = int(document_id)
            user_id = int(user_id)
        except (TypeError, ValueError):
            return {"success": False, "error": f"유효하지 않은 문서 ID 또는 사용자 ID: {document_id}, {user_id}"}
        
        # 문서 처리 실행 (사용자 ID 전달)
        result = asyncio.run(PDFProcessor.process_and_embed_document(
            db=db, 
            document_id=document_id,
            user_id=user_id
        ))
        return result
    except Exception as e:
        logger.error(f"PDF 문서 처리 실패: {str(e)}")
        logger.error(traceback.format_exc())
        return {"success": False, "error": str(e), "document_id": document_id}
    finally:
        # 세션 종료
        db.close()

def wrapper_summarize_document(db=None, document_id=None, level=None, **kwargs):
    """
    PDF 문서 요약 작업 래퍼 함수
    """
    # 직접 세션을 생성하는 대신 인자로 받거나 생성
    use_local_db = db is None
    if use_local_db:
        db = SessionLocal()
    
    try:
        # 모델 초기화를 위한 추가 임포트
        from app.models.user import User
        from app.models.tag import PDFFile, PDFTag, PDFTagMention
        from app.models.task import Task
        from app.services.pdf_agent.ai_agent import PDFAgent
        
        # 작업 실행
        return asyncio.run(PDFAgent.summarize(db=db, document_id=document_id, level=level))
    finally:
        # 로컬에서 생성한 세션만 닫음
        if use_local_db and db:
            db.close()

def wrapper_generate_questions(db=None, document_id=None, count=None, **kwargs):
    """
    PDF 문서 문제 생성 작업 래퍼 함수
    """
    # 직접 세션을 생성하는 대신 인자로 받거나 생성
    use_local_db = db is None
    if use_local_db:
        db = SessionLocal()
        
    try:
        # 모델 초기화를 위한 추가 임포트
        from app.models.user import User
        from app.models.tag import PDFFile, PDFTag, PDFTagMention
        from app.models.task import Task
        from app.services.pdf_agent.ai_agent import PDFAgent
        
        # 작업 실행
        return asyncio.run(PDFAgent.generate_questions(db=db, document_id=document_id, count=count))
    finally:
        # 로컬에서 생성한 세션만 닫음
        if use_local_db and db:
            db.close()

def main():
    try:
        # Redis 연결 확인
        try:
            conn.ping()
            logger.info(f"✅ Redis 연결 성공: {settings.REDIS_URL}")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Redis 연결 실패: {str(e)}")
            sys.exit(1)

        queues = ['pdf_tasks', 'ai_tasks', 'default']
        worker_kwargs = {
            'default_worker_ttl': 420,
            'job_monitoring_interval': 30
        }

        with Connection(conn):
            worker = Worker(
                queues,
                name=f"worker-{os.getpid()}",
                job_class=CustomJob,
                **worker_kwargs
            )
            logger.info(f"워커 시작: {worker.name}, 처리 큐: {', '.join(queues)}")
            worker.work()

    except KeyboardInterrupt:
        logger.info("워커 종료 요청 받음")
        sys.exit(0)
    except Exception as e:
        logger.error(f"워커 오류 발생: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()