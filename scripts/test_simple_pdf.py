import logging
import time
from app.workers.task_manager import TaskManager
from app.scripts.simple_pdf_task import process_pdf_simple

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_simple_pdf')

# 테스트할 PDF 문서 ID 설정
DOCUMENT_ID = 1  # 임의의 ID

# TaskManager 초기화
task_manager = TaskManager()

# 작업 ID 생성
job_id = f'pdf_simple_{int(time.time())}'
logger.info(f'간단한 PDF 처리 작업 등록: {job_id}')

# PDF 처리 작업 등록
task_job_id = task_manager.enqueue_task(
    process_pdf_simple,  # 간단한 PDF 처리 함수
    DOCUMENT_ID,  # 문서 ID
    queue_name='pdf',  # PDF 전용 큐 사용
    job_id=job_id,
    job_timeout=60,  # 1분 제한
    user_id=1,  # 임의의 사용자 ID
    task_type="simple_pdf_process"
)

logger.info(f'등록된 PDF 처리 작업 ID: {task_job_id}')

# 작업 상태 확인
for i in range(30):  # 30초간 대기
    status = task_manager.get_job_status(job_id)
    logger.info(f'작업 상태 ({i+1}/30): {status}')
    time.sleep(1)

    # 작업이 완료되면 종료
    if status.get('status') in ['finished', 'failed']:
        break

logger.info('테스트 완료')
