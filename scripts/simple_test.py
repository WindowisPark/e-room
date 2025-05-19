import time
import logging
from app.workers.task_manager import TaskManager

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('simple_test')

def simple_task(seconds):
    logger.info(f'테스트 작업 시작: {seconds}초 대기')
    time.sleep(seconds)
    result = seconds * 2
    logger.info(f'테스트 작업 완료: 결과 = {result}')
    return result

# TaskManager 초기화
task_manager = TaskManager()

# 작업 ID 생성
job_id = f'simple_{int(time.time())}'
logger.info(f'작업 등록: {job_id}')

# 작업 등록
task_job_id = task_manager.enqueue_task(
    simple_task,
    3,  # 3초 대기
    queue_name='default',
    job_id=job_id
)

logger.info(f'등록된 작업 ID: {task_job_id}')

# 작업 상태 확인
for i in range(10):
    status = task_manager.get_job_status(job_id)
    logger.info(f'작업 상태 ({i+1}/10): {status}')
    time.sleep(1)

logger.info('테스트 완료')
