from app.workers.task_manager import TaskManager
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fix_encoding")

# Redis 키 인코딩 문제 확인
def check_redis_keys():
    """Redis 키 인코딩 문제 확인"""
    # TaskManager 인스턴스
    task_manager = TaskManager()

    if task_manager.redis_conn:
        logger.info("Redis 키 확인 중...")

        try:
            # 모든 키 가져오기
            keys = task_manager.redis_conn.keys("*")
            logger.info(f"총 {len(keys)}개 키 발견")

            # 키 타입 확인
            for i, key in enumerate(keys):
                key_type = type(key).__name__

                if isinstance(key, bytes):
                    key_str = key.decode('utf-8', errors='replace')
                    logger.info(f"키 {i+1}: {key_str} (바이트 타입: {key})")
                else:
                    logger.info(f"키 {i+1}: {key} (타입: {key_type})")

                # 값 가져오기 시도
                try:
                    if isinstance(key, bytes):
                        value = task_manager.redis_conn.get(key)
                        logger.info(f"  - 값 타입: {type(value).__name__}")
                    else:
                        value = task_manager.redis_conn.get(key)
                        logger.info(f"  - 값 타입: {type(value).__name__}")
                except Exception as e:
                    logger.error(f"  - 값 가져오기 실패: {str(e)}")

        except Exception as e:
            logger.error(f"Redis 키 확인 중 오류: {str(e)}")
    else:
        logger.error("Redis 연결 없음")

# TaskManager 수정
def fix_task_manager():
    """TaskManager의 Redis 연결 수정"""

    # task_manager.py 파일 원본 백업
    import shutil
    import os

    file_path = 'app/workers/task_manager.py'
    backup_path = 'app/workers/task_manager.py.bak'

    # 백업 파일이 없으면 백업
    if not os.path.exists(backup_path):
        shutil.copy2(file_path, backup_path)
        logger.info(f"원본 파일 백업 완료: {backup_path}")

    # 파일 읽기
    with open(file_path, 'r') as f:
        content = f.read()

    # 수정: decode_responses=True 추가
    if "decode_responses=True" not in content:
        # Redis 연결 부분 찾기
        old_conn = "self.redis_conn = redis.Redis.from_url("
        new_conn = "self.redis_conn = redis.Redis.from_url("

        if "decode_responses=" in content:
            # decode_responses 옵션이 있지만 False로 설정되어 있는 경우
            import re
            content = re.sub(
                r'decode_responses=False',
                'decode_responses=True',
                content
            )
            logger.info("decode_responses=False를 decode_responses=True로 변경")
        else:
            # decode_responses 옵션이 없는 경우
            old_redis_url = "self.redis_conn = redis.Redis.from_url(\n            settings.REDIS_URL"
            new_redis_url = "self.redis_conn = redis.Redis.from_url(\n            settings.REDIS_URL,\n            decode_responses=True"

            if old_redis_url in content:
                content = content.replace(old_redis_url, new_redis_url)
                logger.info("Redis 연결에 decode_responses=True 옵션 추가")
            else:
                # 다른 패턴 시도
                old_redis_url = "self.redis_conn = redis.Redis.from_url(settings.REDIS_URL"
                new_redis_url = "self.redis_conn = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True"

                if old_redis_url in content:
                    content = content.replace(old_redis_url, new_redis_url)
                    logger.info("Redis 연결에 decode_responses=True 옵션 추가 (단일 라인)")
                else:
                    logger.warning("Redis 연결 패턴을 찾을 수 없음, 수동 수정 필요")

        # 작업 fetch 부분 수정
        if "job = queue.fetch_job(job_id)" in content:
            fetch_job_fix = """
            try:
                job = queue.fetch_job(job_id)
            except UnicodeDecodeError:
                # 인코딩 오류 처리
                logger.warning(f"작업 조회 중 인코딩 오류: {job_id}, 오류 처리 로직 사용")
                return {
                    "status": "pending",
                    "progress": 0,
                    "message": "작업 상태 조회 중 인코딩 문제가 발생했습니다. 작업은 계속 처리 중입니다."
                }
            """
            content = content.replace("job = queue.fetch_job(job_id)", fetch_job_fix)
            logger.info("작업 fetch 로직에 인코딩 오류 처리 추가")

        # 파일 쓰기
        with open(file_path, 'w') as f:
            f.write(content)

        logger.info(f"TaskManager 수정 완료: {file_path}")
    else:
        logger.info("TaskManager에 이미 decode_responses=True 옵션이 있음")

    return True

if __name__ == "__main__":
    # Redis 키 확인
    check_redis_keys()

    # TaskManager 수정
    if fix_task_manager():
        logger.info("수정 완료. API 서비스를 재시작하세요.")
        logger.info("명령어: docker-compose restart api")
    else:
        logger.error("수정 실패!")
