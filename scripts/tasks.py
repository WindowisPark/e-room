import time
import logging

# 로깅 설정
logger = logging.getLogger('tasks')

def simple_task(seconds):
    """
    간단한 테스트 작업 - 지정된 시간만큼 대기 후 결과 반환
    """
    logger.info(f'테스트 작업 시작: {seconds}초 대기')
    time.sleep(seconds)
    result = seconds * 2
    logger.info(f'테스트 작업 완료: 결과 = {result}')
    return result
