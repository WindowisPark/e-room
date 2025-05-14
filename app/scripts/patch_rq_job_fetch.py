import logging
from app.workers.task_manager import TaskManager
import redis
import rq
from rq.job import Job

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("patch_rq")

def custom_fetch_job(job_id, connection=None):
    """
    RQ의 Job.fetch 함수를 대체하는 안전한 버전
    """
    try:
        # 원래 방식으로 시도
        return Job.fetch(job_id, connection=connection)
    except Exception as e:
        logger.error(f"Job.fetch 실패: {str(e)}, 대체 방법 시도")
        
        # 대체 방법: 직접 Redis에서 작업 데이터 조회
        try:
            job_key = f"rq:job:{job_id}"
            
            # Redis 연결이 없으면 생성
            if connection is None:
                connection = redis.Redis(host='redis', port=6379, decode_responses=True)
            
            # 작업 존재 여부 확인
            if not connection.exists(job_key):
                logger.warning(f"작업 키가 존재하지 않음: {job_key}")
                return None
            
            # 작업 상태 확인
            job = Job(job_id, connection=connection)
            
            # 안전하게 상태 가져오기
            try:
                status = job.get_status()
                logger.info(f"작업 상태 확인 성공: {status}")
            except Exception as status_error:
                logger.error(f"작업 상태 가져오기 실패: {str(status_error)}")
                # 기본 상태 설정
                job._status = "unknown"
            
            # 안전하게 메타데이터 설정
            try:
                job.meta = {"progress": 0, "message": "상태 정보 복구됨"}
            except Exception as meta_error:
                logger.error(f"메타데이터 설정 실패: {str(meta_error)}")
            
            return job
            
        except Exception as alt_error:
            logger.error(f"대체 방법도 실패: {str(alt_error)}")
            return None

# TaskManager의 get_job_status 함수 패치
def patch_task_manager():
    """TaskManager의 get_job_status 함수 패치"""
    # 기존 TaskManager 인스턴스
    task_manager = TaskManager()
    
    # 원본 함수 저장
    original_get_job_status = task_manager.get_job_status
    
    # 패치된 함수
    def patched_get_job_status(job_id):
        try:
            # Redis 연결 확인
            if task_manager.redis_conn is None:
                logger.warning(f"Redis 연결 없음: 작업 {job_id} 상태 조회 불가")
                return {
                    "status": "unknown",
                    "progress": 0,
                    "message": "Redis 연결 없음 (개발 모드)"
                }
            
            # 큐 가져오기
            queues = list(task_manager.queues.values())
            if not queues:
                logger.error("사용 가능한 큐가 없음")
                return {"status": "error", "message": "사용 가능한 큐가 없음"}
            
            # 첫 번째 큐 사용
            queue = queues[0]
            
            # 작업 조회 시도 (패치된 함수 사용)
            job = custom_fetch_job(job_id, connection=task_manager.redis_conn)
            
            if not job:
                logger.warning(f"작업을 찾을 수 없음: {job_id}")
                return {"status": "not_found"}
            
            # 상태 및 메타데이터 가져오기
            try:
                status = job.get_status()
            except Exception as e:
                logger.error(f"작업 상태 가져오기 실패: {str(e)}")
                status = "unknown"
            
            try:
                meta = job.meta if hasattr(job, 'meta') else {}
            except Exception as e:
                logger.error(f"작업 메타데이터 가져오기 실패: {str(e)}")
                meta = {"progress": 0}
            
            # 결과 가져오기
            result = None
            if status == "finished":
                try:
                    result = job.result
                except Exception as e:
                    logger.error(f"작업 결과 가져오기 실패: {str(e)}")
            
            # 오류 정보 가져오기
            error = None
            if status == "failed":
                try:
                    error = job.exc_info
                except Exception as e:
                    logger.error(f"작업 오류 정보 가져오기 실패: {str(e)}")
            
            # 상태 정보 반환
            return {
                "status": status,
                "progress": meta.get("progress", 0),
                "result": result,
                "error": error,
                "created_at": meta.get("created_at"),
                "message": meta.get("message", "작업 진행 중")
            }
            
        except Exception as e:
            logger.error(f"작업 상태 조회 실패: {str(e)}")
            return {"status": "error", "message": str(e)}
    
    # 함수 교체
    task_manager.get_job_status = patched_get_job_status
    
    logger.info("TaskManager.get_job_status 함수가 패치되었습니다.")
    return task_manager

# 실행
if __name__ == "__main__":
    logger.info("RQ 작업 조회 함수 패치 중...")
    patched_task_manager = patch_task_manager()
    
    # 테스트
    job_id = "test_task_1747163988"  # 이전에 생성된 작업 ID
    logger.info(f"패치된 함수로 작업 상태 조회: {job_id}")
    status = patched_task_manager.get_job_status(job_id)
    logger.info(f"조회 결과: {status}")
    
    logger.info("패치 완료!")
    logger.info("이 패치는 현재 프로세스에만 적용됩니다.")
    logger.info("영구적으로 적용하려면 task_manager.py 파일을 수정하세요.")
