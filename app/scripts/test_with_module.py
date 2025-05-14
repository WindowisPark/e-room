import time
import logging
from app.workers.task_manager import TaskManager
from app.scripts.tasks import simple_task  # 별도 모듈에서 가져옴

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_with_module')

# TaskManager 초기화
task_manager = TaskManager()

# 작업 ID 생성
job_id = f'simple_{int(time.time())}'
logger.info(f'작업 등록: {job_id}')

# 작업 등록 - 별도 모듈의 함수 사용
task_job_id = task_manager.enqueue_task(
    simple_task,
    3,  # 3초 대기
    queue_name='default',
    job_id=job_id
)

logger.info(f'등록된 작업 ID: {task_job_id}')

# 작업 상태 확인
for i in range(15):  # 더 오래 기다림
    status = task_manager.get_job_status(job_id)
    logger.info(f'작업 상태 ({i+1}/15): {status}')
    time.sleep(1)

logger.info('테스트 완료')
