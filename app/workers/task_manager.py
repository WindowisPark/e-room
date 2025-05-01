import uuid
import json
import logging
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
import redis
import rq
from rq.job import Job

from app.core.config import settings

logger = logging.getLogger(__name__)

class TaskManager:
    """
    비동기 작업 관리 클래스
    - Redis 기반 작업 큐 관리
    - 작업 상태 조회 및 업데이트
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TaskManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Redis 연결 및 큐 초기화"""
        try:
            self.redis_conn = redis.Redis.from_url(
                settings.REDIS_URL, 
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            self.redis_conn.ping()  # 연결 확인
            
            # 작업 큐 정의
            self.queues = {
                "pdf": rq.Queue("pdf_tasks", connection=self.redis_conn),
                "ai": rq.Queue("ai_tasks", connection=self.redis_conn),
                "default": rq.Queue("default", connection=self.redis_conn)
            }
            
            logger.info("TaskManager 초기화 완료")
        except redis.RedisError as e:
            logger.error(f"Redis 연결 실패: {str(e)}")
            # 오류 발생 시 더미 구현으로 대체 (개발용)
            self.redis_conn = None
            self.queues = {
                "pdf": DummyQueue(),
                "ai": DummyQueue(),
                "default": DummyQueue()
            }
    
    def enqueue_task(
        self, 
        func: Callable, 
        *args, 
        queue_name: str = "default", 
        job_id: Optional[str] = None, 
        job_timeout: int = 3600,
        **kwargs
    ) -> str:
        """
        작업 큐에 태스크 등록
        
        Args:
            func: 실행할 함수
            args: 함수 인자
            queue_name: 큐 이름 (default, pdf, ai)
            job_id: 작업 ID (None인 경우 자동 생성)
            job_timeout: 작업 타임아웃 (초)
            kwargs: 함수 키워드 인자
            
        Returns:
            작업 ID
        """
        job_id = job_id or f"task_{uuid.uuid4()}"
        
        try:
            queue = self.queues.get(queue_name, self.queues["default"])
            
            # Redis 연결이 없는 경우 (개발/테스트 환경)
            if self.redis_conn is None:
                logger.warning(f"Redis 연결 없음: 작업 {job_id}가 큐에 추가되었다고 가정")
                return job_id
            
            # 작업 메타데이터 설정
            meta = {
                "created_at": datetime.utcnow().isoformat(),
                "progress": 0,
                "status": "queued"
            }
            
            # 작업 등록
            job = queue.enqueue(
                func,
                *args,
                **kwargs,
                job_id=job_id,
                timeout=job_timeout,
                result_ttl=86400,  # 결과 24시간 유지
                meta=meta
            )
            
            logger.info(f"작업 등록 성공: {job_id} (큐: {queue_name})")
            return job_id
            
        except Exception as e:
            logger.error(f"작업 등록 실패: {str(e)}")
            return job_id  # 실패해도 ID 반환 (클라이언트 처리 일관성)
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        작업 상태 조회
        
        Args:
            job_id: 작업 ID
            
        Returns:
            작업 상태 정보
        """
        try:
            # Redis 연결이 없는 경우 (개발/테스트 환경)
            if self.redis_conn is None:
                logger.warning(f"Redis 연결 없음: 작업 {job_id}의 상태 조회 불가")
                return {
                    "status": "unknown",
                    "progress": 0,
                    "message": "Redis 연결 없음 (개발 모드)"
                }
            
            # 모든 큐에서 작업 찾기
            job = None
            for queue_name, queue in self.queues.items():
                job = queue.fetch_job(job_id)
                if job:
                    break
            
            if not job:
                return {"status": "not_found"}
                
            return {
                "status": job.get_status(),
                "progress": job.meta.get("progress", 0),
                "result": job.result if job.is_finished else None,
                "error": job.exc_info if job.is_failed else None,
                "created_at": job.meta.get("created_at"),
                "updated_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"작업 상태 조회 실패: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    def update_job_progress(self, job_id: str, progress: int, message: Optional[str] = None) -> bool:
        """
        작업 진행 상태 업데이트
        
        Args:
            job_id: 작업 ID
            progress: 진행률 (0-100)
            message: 상태 메시지
            
        Returns:
            성공 여부
        """
        try:
            # Redis 연결이 없는 경우 (개발/테스트 환경)
            if self.redis_conn is None:
                logger.warning(f"Redis 연결 없음: 작업 {job_id}의 진행 상태 업데이트 불가")
                return False
            
            # 모든 큐에서 작업 찾기
            job = None
            for queue_name, queue in self.queues.items():
                job = queue.fetch_job(job_id)
                if job:
                    break
            
            if not job:
                return False
            
            # 메타데이터 업데이트
            job.meta["progress"] = progress
            if message:
                job.meta["message"] = message
            job.meta["updated_at"] = datetime.utcnow().isoformat()
            job.save_meta()
            
            logger.debug(f"작업 진행 상태 업데이트: {job_id} ({progress}%)")
            return True
            
        except Exception as e:
            logger.error(f"작업 진행 상태 업데이트 실패: {str(e)}")
            return False
    
    def fetch_jobs(self, queue_name: str = "default", status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        큐에서 작업 목록 조회
        
        Args:
            queue_name: 큐 이름
            status: 작업 상태 필터 (None인 경우 모든 작업)
            
        Returns:
            작업 목록
        """
        try:
            # Redis 연결이 없는 경우 (개발/테스트 환경)
            if self.redis_conn is None:
                logger.warning(f"Redis 연결 없음: 큐 {queue_name}의 작업 목록 조회 불가")
                return []
            
            queue = self.queues.get(queue_name, self.queues["default"])
            
            # 상태별 작업 조회
            if status == "failed":
                jobs = queue.failed_job_registry.get_job_ids()
            elif status == "scheduled":
                jobs = queue.scheduled_job_registry.get_job_ids()
            elif status == "finished":
                jobs = queue.finished_job_registry.get_job_ids()
            elif status == "started":
                jobs = queue.started_job_registry.get_job_ids()
            else:
                # 모든 작업 ID 조회 - Registry 순회
                jobs = []
                for registry in [
                    queue.started_job_registry,
                    queue.scheduled_job_registry,
                    queue.finished_job_registry,
                    queue.failed_job_registry
                ]:
                    jobs.extend(registry.get_job_ids())
            
            # 작업 상세 정보 조회
            result = []
            for job_id in jobs:
                job = queue.fetch_job(job_id)
                if job:
                    result.append({
                        "id": job.id,
                        "status": job.get_status(),
                        "progress": job.meta.get("progress", 0),
                        "created_at": job.meta.get("created_at"),
                        "updated_at": job.meta.get("updated_at")
                    })
            
            return result
            
        except Exception as e:
            logger.error(f"작업 목록 조회 실패: {str(e)}")
            return []


# 개발/테스트용 더미 큐 클래스
class DummyQueue:
    """Redis 없이 개발할 때 사용하는 더미 큐"""
    
    def __init__(self):
        self.jobs = {}
    
    def enqueue(self, func, *args, job_id=None, **kwargs):
        """작업 등록 (더미)"""
        job_id = job_id or f"dummy_{uuid.uuid4()}"
        self.jobs[job_id] = {
            "func": func.__name__,
            "args": args,
            "kwargs": kwargs,
            "status": "queued",
            "meta": {
                "progress": 0,
                "created_at": datetime.utcnow().isoformat()
            }
        }
        return DummyJob(job_id)
    
    def fetch_job(self, job_id):
        """작업 조회 (더미)"""
        if job_id in self.jobs:
            job_data = self.jobs[job_id]
            return DummyJob(
                job_id,
                status=job_data["status"],
                meta=job_data["meta"]
            )
        return None


# 개발/테스트용 더미 작업 클래스
class DummyJob:
    """Redis 없이 개발할 때 사용하는 더미 작업"""
    
    def __init__(self, id, status="queued", meta=None, result=None, exc_info=None):
        self.id = id
        self._status = status
        self.meta = meta or {"progress": 0}
        self.result = result
        self.exc_info = exc_info
    
    def get_status(self):
        """상태 조회 (더미)"""
        return self._status
    
    def is_finished(self):
        """완료 여부 조회 (더미)"""
        return self._status == "finished"
    
    def is_failed(self):
        """실패 여부 조회 (더미)"""
        return self._status == "failed"
    
    def save_meta(self):
        """메타데이터 저장 (더미)"""
        pass