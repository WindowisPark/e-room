from app.workers.task_manager import TaskManager
from app.scripts.tasks import test_func  # 별도 모듈에서 가져옴
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_task_manager")

# TaskManager 초기화
task_manager = TaskManager()

# 테스트 작업 등록
job_id = "test_task_" + str(int(time.time()))
logger.info(f"작업 등록: {job_id}")

task_job_id = task_manager.enqueue_task(
    test_func,
    42,
    queue_name="default",
    job_id=job_id,
    job_timeout=30
)

logger.info(f"등록된 작업 ID: {task_job_id}")

# 작업 상태 확인
for i in range(20):  # 좀 더 길게 기다림
    time.sleep(1)
    status = task_manager.get_job_status(job_id)
    logger.info(f"작업 상태 ({i+1}/20): {status}")

    if status.get('status') == 'finished':
        logger.info(f"작업 결과: {status.get('result')}")
        break

logger.info("테스트 완료")
