# app/workers/worker.py
#!/usr/bin/env python
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
from rq.worker import HerokuWorker, WorkerStatus

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.notification_service import send_notification

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('worker')

# Redis 연결 설정
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# 작업 처리 전 작업
def before_job_hook(job, *args, **kwargs):
    """
    작업 처리 전 수행할 동작
    """
    logger.info(f"작업 시작: {job.id}, 큐: {job.origin}, 함수: {job.func_name}")
    
    # 작업 상태 업데이트
    job.meta['status'] = 'processing'
    job.meta['progress'] = 0
    job.meta['started_at'] = time.time()
    job.save_meta()

# 작업 처리 후 작업
def after_job_hook(job, connection, result, *args, **kwargs):
    """
    작업 처리 완료 후 수행할 동작
    """
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
    
    # 작업 완료 알림 전송 (선택적)
    try:
        if not job.is_failed and 'user_id' in job.kwargs:
            db = SessionLocal()
            user_id = job.kwargs.get('user_id')
            
            # 사용자에게 작업 완료 알림 전송
            send_notification(
                db=db,
                user_id=user_id,
                type="system",
                message=f"작업이 완료되었습니다: {job.description}",
                link=f"/tasks/{job.id}/result"
            )
            
            db.close()
    except Exception as e:
        logger.error(f"알림 전송 실패: {str(e)}")

# 작업 실패 처리
def handle_job_failure(job, *args, **kwargs):
    """
    작업 실패 시 수행할 동작
    """
    logger.error(f"작업 실패 처리: {job.id}, 오류: {job.exc_info}")
    
    # 작업 상태 업데이트
    job.meta['status'] = 'failed'
    job.meta['error'] = job.exc_info
    job.meta['failed_at'] = time.time()
    job.save_meta()
    
    # 실패 알림 전송 (선택적)
    try:
        if 'user_id' in job.kwargs:
            db = SessionLocal()
            user_id = job.kwargs.get('user_id')
            
            # 사용자에게 작업 실패 알림 전송
            send_notification(
                db=db,
                user_id=user_id,
                type="system",
                message=f"작업 처리 중 오류가 발생했습니다: {job.description}",
                link=f"/tasks/{job.id}/result"
            )
            
            db.close()
    except Exception as e:
        logger.error(f"실패 알림 전송 오류: {str(e)}")

def main():
    """
    메인 워커 프로세스 함수
    """
    try:
        # Redis 연결
        conn = Redis(
            host=REDIS_HOST,
            port=REDIS_PORT,
            db=REDIS_DB
        )
        
        # 큐 목록 정의
        queues = ['pdf_tasks', 'ai_tasks', 'default']
        
        # 워커 옵션 설정
        worker_kwargs = {
            'default_worker_ttl': 420,
            'job_monitoring_interval': 30
        }
        
        # Redis 연결 테스트
        try:
            conn.ping()
            logger.info(f"Redis 연결 성공: {REDIS_HOST}:{REDIS_PORT}")
        except redis.exceptions.ConnectionError as e:
            logger.error(f"Redis 연결 실패: {str(e)}")
            sys.exit(1)
        
        # 워커 실행
        with Connection(conn):
            worker = Worker(
                queues,
                name=f"worker-{os.getpid()}",
                **worker_kwargs
            )
            
            # 처리기 등록
            worker.push_exc_handler(handle_job_failure)
            worker.push_job_hook('before_job', before_job_hook)
            worker.push_job_hook('after_job', after_job_hook)
            
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