# app/core/redis_helper.py

import os
import logging
import json
from typing import Dict, Any, Optional
from functools import lru_cache
from datetime import datetime, timedelta

# 동기식 Redis 클라이언트
from redis import Redis, RedisError
# 비동기식 Redis 클라이언트 (WebSocket 실시간 협업용)
import redis.asyncio as aioredis

# 로깅 설정
logger = logging.getLogger(__name__)

# 환경 변수에서 Redis 설정 로드
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))

# 동기식 Redis 클라이언트 초기화
try:
    redis_client = Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True,
        socket_connect_timeout=3,   # 3초 안에 연결 안되면 실패
        socket_timeout=3,           # 명령 실행 3초 제한
        retry_on_timeout=False      # 타임아웃 시 재시도 안함
    )
    redis_client.ping()
    logger.info("✅ Redis 연결 성공")
except RedisError as e:
    logger.error(f"⚠️ Redis 연결 실패: {str(e)}")
    redis_client = None

# ------------------------------------------------------
# 출석 체크 관련 함수
# ------------------------------------------------------

def is_attendance_checked(user_id: int) -> bool:
    """
    Redis에 오늘 출석 여부 확인
    """
    if not redis_client:
        logger.warning("Redis 클라이언트 없음")
        return False

    today = datetime.now().strftime("%Y-%m-%d")
    key = f"attendance:{today}"
    return redis_client.sismember(key, user_id)


def mark_attendance(user_id: int):
    """
    Redis에 출석 기록 저장
    """
    if not redis_client:
        logger.warning("Redis 클라이언트 없음")
        return

    today = datetime.now().strftime("%Y-%m-%d")
    key = f"attendance:{today}"

    try:
        redis_client.sadd(key, user_id)  # 사용자 출석 추가
        # 자정까지 만료 설정
        expire_at = datetime.combine(datetime.now().date() + timedelta(days=1), datetime.min.time())
        redis_client.expireat(key, int(expire_at.timestamp()))
        logger.info(f"출석 체크됨 - User ID: {user_id}")
    except RedisError as e:
        logger.error(f"출석 체크 실패 - User ID: {user_id}, Error: {str(e)}")


def get_daily_attendance() -> list:
    """
    오늘 출석한 모든 사용자 목록 조회
    """
    if not redis_client:
        logger.warning("Redis 클라이언트 없음")
        return []

    today = datetime.now().strftime("%Y-%m-%d")
    key = f"attendance:{today}"

    try:
        return list(redis_client.smembers(key))
    except RedisError as e:
        logger.error(f"출석 목록 조회 실패: {str(e)}")
        return []

# ------------------------------------------------------
# 일반적인 Redis 유틸리티 함수
# ------------------------------------------------------

def set_key(key: str, value: str, expire_seconds: int = None):
    """
    Redis에 키-값 쌍 저장
    """
    if not redis_client:
        logger.warning("Redis 클라이언트 없음")
        return

    try:
        redis_client.set(key, value, ex=expire_seconds)
        logger.info(f"Redis 키 저장됨 - {key}")
    except RedisError as e:
        logger.error(f"Redis 키 저장 실패 - {key}, Error: {str(e)}")


def get_key(key: str) -> str:
    """
    Redis에서 키 조회
    """
    if not redis_client:
        logger.warning("Redis 클라이언트 없음")
        return None

    try:
        return redis_client.get(key)
    except RedisError as e:
        logger.error(f"Redis 키 조회 실패 - {key}, Error: {str(e)}")
        return None


def delete_key(key: str):
    """
    Redis에서 키 삭제
    """
    if not redis_client:
        logger.warning("Redis 클라이언트 없음")
        return

    try:
        redis_client.delete(key)
        logger.info(f"Redis 키 삭제됨 - {key}")
    except RedisError as e:
        logger.error(f"Redis 키 삭제 실패 - {key}, Error: {str(e)}")
        
# ------------------------------------------------------
# 비동기 Redis 클라이언트 (실시간 협업용)
# ------------------------------------------------------

@lru_cache()
def get_redis_client() -> aioredis.Redis:
    """
    비동기 Redis 클라이언트 인스턴스 반환 (싱글톤 패턴)
    WebSocket 연결 관리에 사용됨
    """
    return aioredis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        decode_responses=True  # 응답을 자동으로 디코딩
    )

async def publish_message(channel: str, message: Dict[str, Any]) -> int:
    """
    Redis 채널에 JSON 메시지 발행
    
    Args:
        channel: 메시지를 발행할 채널명
        message: JSON 직렬화 가능한 딕셔너리 메시지
        
    Returns:
        메시지를 받은 클라이언트 수
    """
    redis_client = get_redis_client()
    try:
        # 딕셔너리를 JSON 문자열로 변환
        message_str = json.dumps(message)
        return await redis_client.publish(channel, message_str)
    except Exception as e:
        logger.error(f"Redis 메시지 발행 실패 - 채널: {channel}, 오류: {str(e)}")
        return 0

async def subscribe_channel(channel: str) -> aioredis.client.PubSub:
    """
    Redis 채널 구독
    
    Args:
        channel: 구독할 채널명
        
    Returns:
        PubSub 인스턴스
    """
    redis_client = get_redis_client()
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(channel)
    return pubsub

async def get_channel_messages(pubsub: aioredis.client.PubSub):
    """
    채널에서 메시지 수신 (비동기 제너레이터)
    
    Args:
        pubsub: PubSub 인스턴스
        
    Yields:
        수신된, 파싱된 JSON 메시지
    """
    async for message in pubsub.listen():
        # 메시지 타입이 'message'인 경우만 처리
        if message['type'] == 'message':
            try:
                # JSON 문자열을 딕셔너리로 변환
                data = json.loads(message['data'])
                yield data
            except Exception as e:
                logger.error(f"⚠️ Redis 메시지 파싱 실패: {str(e)}")

async def get_team_presence(team_id: str) -> list:
    """
    팀스페이스에 현재 접속 중인 사용자 목록 조회
    
    Args:
        team_id: 팀 ID
        
    Returns:
        접속 중인 사용자 ID 목록
    """
    redis_client = get_redis_client()
    key = f"team_presence:{team_id}"
    try:
        # Set에 저장된 모든 사용자 ID 가져오기
        members = await redis_client.smembers(key)
        return list(members)
    except Exception as e:
        logger.error(f"팀 접속자 목록 조회 실패 - 팀 ID: {team_id}, 오류: {str(e)}")
        return []

async def add_user_to_team_presence(team_id: str, user_id: str, expiry_seconds: int = 300):
    """
    팀스페이스 접속자 목록에 사용자 추가 (일정 시간 후 자동 만료)
    
    Args:
        team_id: 팀 ID
        user_id: 사용자 ID
        expiry_seconds: 만료 시간(초), 기본 5분
    """
    redis_client = get_redis_client()
    key = f"team_presence:{team_id}"
    
    try:
        # Set에 사용자 ID 추가
        await redis_client.sadd(key, user_id)
        
        # 사용자별 만료 시간 설정
        user_key = f"team_presence:{team_id}:user:{user_id}"
        await redis_client.set(user_key, "1", ex=expiry_seconds)
        
        # 만료 시 자동으로 Set에서 제거하는 스크립트 등록
        script = """
        if redis.call('exists', KEYS[2]) == 0 then
            return redis.call('srem', KEYS[1], ARGV[1])
        end
        return 0
        """
        await redis_client.eval(
            script, 
            2,  # 키 개수
            key,  # KEYS[1]
            user_key,  # KEYS[2]
            user_id  # ARGV[1]
        )
    except Exception as e:
        logger.error(f"팀 접속자 추가 실패 - 팀 ID: {team_id}, 사용자 ID: {user_id}, 오류: {str(e)}")

async def remove_user_from_team_presence(team_id: str, user_id: str):
    """
    팀스페이스 접속자 목록에서 사용자 제거
    
    Args:
        team_id: 팀 ID
        user_id: 사용자 ID
    """
    redis_client = get_redis_client()
    key = f"team_presence:{team_id}"
    user_key = f"team_presence:{team_id}:user:{user_id}"
    
    try:
        # Set에서 사용자 ID 제거
        await redis_client.srem(key, user_id)
        # 사용자 만료 키도 제거
        await redis_client.delete(user_key)
    except Exception as e:
        logger.error(f"팀 접속자 제거 실패 - 팀 ID: {team_id}, 사용자 ID: {user_id}, 오류: {str(e)}")

async def store_cursor_position(team_id: str, user_id: str, pdf_id: str, page: int, position: Dict[str, float], expiry_seconds: int = 60):
    """
    사용자의 현재 커서 위치 저장
    
    Args:
        team_id: 팀 ID
        user_id: 사용자 ID
        pdf_id: PDF 문서 ID
        page: 페이지 번호
        position: 커서 위치 좌표 (x, y)
        expiry_seconds: 만료 시간(초), 기본 1분
    """
    redis_client = get_redis_client()
    key = f"cursor_position:{team_id}:{pdf_id}:{user_id}"
    
    try:
        data = {
            "page": page,
            "position": position,
            "updated_at": datetime.now().isoformat()
        }
        # JSON으로 변환하여 저장
        await redis_client.set(key, json.dumps(data), ex=expiry_seconds)
    except Exception as e:
        logger.error(f"커서 위치 저장 실패 - 팀 ID: {team_id}, 사용자 ID: {user_id}, 오류: {str(e)}")

async def get_all_cursor_positions(team_id: str, pdf_id: str) -> Dict[str, Any]:
    """
    특정 PDF 문서에 대한 모든 사용자의 커서 위치 조회
    
    Args:
        team_id: 팀 ID
        pdf_id: PDF 문서 ID
        
    Returns:
        사용자 ID를 키로 하고 커서 위치 정보를 값으로 하는 딕셔너리
    """
    redis_client = get_redis_client()
    pattern = f"cursor_position:{team_id}:{pdf_id}:*"
    
    try:
        # 패턴에 일치하는 모든 키 조회
        cursor = 0
        result = {}
        
        while True:
            cursor, keys = await redis_client.scan(cursor, match=pattern)
            
            for key in keys:
                # 키에서 사용자 ID 추출
                user_id = key.split(":")[-1]
                # 커서 위치 데이터 조회
                position_data = await redis_client.get(key)
                if position_data:
                    result[user_id] = json.loads(position_data)
            
            if cursor == 0:
                break
        
        return result
    except Exception as e:
        logger.error(f"커서 위치 조회 실패 - 팀 ID: {team_id}, PDF ID: {pdf_id}, 오류: {str(e)}")
        return {}