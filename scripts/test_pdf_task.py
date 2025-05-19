import logging
import time
from app.workers.task_manager import TaskManager
from app.scripts.pdf_task_wrapper import process_pdf_document

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test_pdf_task')

# 테스트할 PDF 문서 ID 설정
# (이 문서 ID가 실제로 존재해야 함)
DOCUMENT_ID = 1  # 적절한 문서 ID로 변경해주세요

# TaskManager 초기화
task_manager = TaskManager()

# 작업 ID 생성
job_id = f'pdf_process_{int(time.time())}'
logger.info(f'PDF 처리 작업 등록: {job_id}')

# PDF 처리 작업 등록
task_job_id = task_manager.enqueue_task(
    process_pdf_document,  # 래핑 함수 사용
    DOCUMENT_ID,  # 문서 ID
    queue_name='pdf',  # PDF 전용 큐 사용
    job_id=job_id,
    job_timeout=1800,  # 30분 제한
    user_id=1,  # 관리자 사용자 ID로 가정
    task_type="process_document",
    document_id=DOCUMENT_ID
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
