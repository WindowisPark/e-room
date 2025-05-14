# app/scripts/test_queue.py
import os
import sys
import time
from pathlib import Path

from redis import Redis
from rq import Queue

def test_func(x):
    """테스트 함수 - 몇 초 대기 후 결과 반환"""
    print(f"테스트 함수 실행 중: 입력값 {x}")
    time.sleep(5)  # 5초 대기
    result = x * x
    print(f"테스트 함수 결과: {result}")
    return result

def main():
    """테스트 메인 함수"""
    print("RQ 작업 큐 테스트 시작...")
    
    # Redis 연결
    redis_host = os.getenv("REDIS_HOST", "redis")
    redis_port = int(os.getenv("REDIS_PORT", 6379))
    
    print(f"Redis 연결 시도: {redis_host}:{redis_port}")
    
    try:
        conn = Redis(host=redis_host, port=redis_port)
        conn.ping()  # 연결 테스트
        print("Redis 연결 성공!")
        
        # 테스트 큐 생성
        queue = Queue("test_queue", connection=conn)
        
        # 작업 추가
        job_id = "test_job_" + str(int(time.time()))
        print(f"작업 추가 시도: {job_id}")
        job = queue.enqueue(test_func, 42, job_id=job_id, timeout=60)
        
        print(f"작업 추가 성공: {job.id}")
        print(f"초기 작업 상태: {job.get_status()}")
        
        # 작업 처리 대기
        for i in range(10):
            time.sleep(1)
            job = queue.fetch_job(job_id)
            if job is None:
                print(f"오류: 작업을 찾을 수 없음 ({i+1}/10)")
                continue
                
            status = job.get_status()
            print(f"작업 상태 ({i+1}/10): {status}")
            
            if status == "finished":
                print(f"작업 결과: {job.result}")
                break
        
        # Redis 키 확인
        print("\nRedis 키 확인:")
        keys = conn.keys("*")
        for i, key in enumerate(keys):
            if isinstance(key, bytes):
                key = key.decode("utf-8")
            print(f"{i+1}. {key}")
            
        print("\n테스트 완료!")
        
    except Exception as e:
        print(f"테스트 실패: {str(e)}")
        
if __name__ == "__main__":
    main()