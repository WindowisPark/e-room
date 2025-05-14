# app/services/cache_service.py

import json
import logging
from typing import Any, Dict, List, Optional, Union, TypeVar, Generic, Callable
from datetime import datetime, timedelta
import redis
from functools import wraps

from app.core.config import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')

class CacheService:
    """
    통합 캐싱 서비스
    
    여러 서비스에서 공통으로 사용할 수 있는 Redis 기반 캐싱 기능 제공
    캐시 키 프리픽스, TTL 등을 관리하고 일관된 인터페이스를 제공합니다.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CacheService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Redis 연결 초기화"""
        try:
            # 캐시용 Redis 연결
            self.redis_client = redis.Redis(
                host=settings.REDIS_CACHE_HOST,
                port=settings.REDIS_CACHE_PORT,
                db=settings.REDIS_CACHE_DB,
                decode_responses=True,
                socket_connect_timeout=3,
                socket_timeout=3
            )
            
            # 연결 테스트
            self.redis_client.ping()
            logger.info("캐시 서비스 Redis 연결 성공")
            
        except redis.RedisError as e:
            logger.error(f"캐시 서비스 Redis 연결 실패: {str(e)}")
            self.redis_client = None
    
    def get(self, key: str, prefix: str = "") -> Optional[str]:
        """
        캐시에서 값 조회
        
        Args:
            key: 캐시 키
            prefix: 키 프리픽스 (기본값: "")
            
        Returns:
            캐시된 값 또는 None
        """
        if not self.redis_client:
            return None
            
        full_key = f"{prefix}:{key}" if prefix else key
        
        try:
            return self.redis_client.get(full_key)
        except redis.RedisError as e:
            logger.error(f"캐시 조회 실패 - 키: {full_key}, 오류: {str(e)}")
            return None
    
    def set(self, key: str, value: str, ttl: int = 300, prefix: str = "") -> bool:
        """
        캐시에 값 저장
        
        Args:
            key: 캐시 키
            value: 저장할 값
            ttl: 만료 시간(초) (기본값: 300초)
            prefix: 키 프리픽스 (기본값: "")
            
        Returns:
            성공 여부
        """
        if not self.redis_client:
            return False
            
        full_key = f"{prefix}:{key}" if prefix else key
        
        try:
            return bool(self.redis_client.setex(full_key, ttl, value))
        except redis.RedisError as e:
            logger.error(f"캐시 저장 실패 - 키: {full_key}, 오류: {str(e)}")
            return False
    
    def delete(self, key: str, prefix: str = "") -> bool:
        """
        캐시에서 키 삭제
        
        Args:
            key: 캐시 키
            prefix: 키 프리픽스 (기본값: "")
            
        Returns:
            성공 여부
        """
        if not self.redis_client:
            return False
            
        full_key = f"{prefix}:{key}" if prefix else key
        
        try:
            return bool(self.redis_client.delete(full_key))
        except redis.RedisError as e:
            logger.error(f"캐시 삭제 실패 - 키: {full_key}, 오류: {str(e)}")
            return False
    
    def exists(self, key: str, prefix: str = "") -> bool:
        """
        캐시에 키가 존재하는지 확인
        
        Args:
            key: 캐시 키
            prefix: 키 프리픽스 (기본값: "")
            
        Returns:
            존재 여부
        """
        if not self.redis_client:
            return False
            
        full_key = f"{prefix}:{key}" if prefix else key
        
        try:
            return bool(self.redis_client.exists(full_key))
        except redis.RedisError as e:
            logger.error(f"캐시 존재 확인 실패 - 키: {full_key}, 오류: {str(e)}")
            return False
    
    def get_json(self, key: str, prefix: str = "") -> Optional[Dict[str, Any]]:
        """
        JSON 형식의 캐시 데이터 조회
        
        Args:
            key: 캐시 키
            prefix: 키 프리픽스 (기본값: "")
            
        Returns:
            디코딩된 JSON 데이터 또는 None
        """
        data = self.get(key, prefix)
        if not data:
            return None
            
        try:
            return json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(f"JSON 디코딩 실패 - 키: {key}, 오류: {str(e)}")
            return None
    
    def set_json(self, key: str, value: Dict[str, Any], ttl: int = 300, prefix: str = "") -> bool:
        """
        JSON 형식으로 캐시 데이터 저장
        
        Args:
            key: 캐시 키
            value: 저장할 JSON 직렬화 가능한 객체
            ttl: 만료 시간(초) (기본값: 300초)
            prefix: 키 프리픽스 (기본값: "")
            
        Returns:
            성공 여부
        """
        try:
            json_data = json.dumps(value)
            return self.set(key, json_data, ttl, prefix)
        except (TypeError, json.JSONDecodeError) as e:
            logger.error(f"JSON 인코딩 실패 - 키: {key}, 오류: {str(e)}")
            return False
    
    def get_list(self, key: str, prefix: str = "") -> List[str]:
        """
        리스트 형식의 캐시 데이터 조회
        
        Args:
            key: 캐시 키
            prefix: 키 프리픽스 (기본값: "")
            
        Returns:
            리스트 데이터 또는 빈 리스트
        """
        if not self.redis_client:
            return []
            
        full_key = f"{prefix}:{key}" if prefix else key
        
        try:
            return self.redis_client.lrange(full_key, 0, -1)
        except redis.RedisError as e:
            logger.error(f"리스트 캐시 조회 실패 - 키: {full_key}, 오류: {str(e)}")
            return []
    
    def add_to_list(self, key: str, value: str, ttl: int = 300, prefix: str = "") -> bool:
        """
        리스트에 값 추가 및 TTL 설정
        
        Args:
            key: 캐시 키
            value: 추가할 값
            ttl: 만료 시간(초) (기본값: 300초)
            prefix: 키 프리픽스 (기본값: "")
            
        Returns:
            성공 여부
        """
        if not self.redis_client:
            return False
            
        full_key = f"{prefix}:{key}" if prefix else key
        
        try:
            pipeline = self.redis_client.pipeline()
            pipeline.rpush(full_key, value)
            pipeline.expire(full_key, ttl)
            pipeline.execute()
            return True
        except redis.RedisError as e:
            logger.error(f"리스트 캐시 추가 실패 - 키: {full_key}, 오류: {str(e)}")
            return False
    
    def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None, prefix: str = "") -> Optional[int]:
            """
            캐시 값 증가
            
            Args:
                key: 캐시 키
                amount: 증가시킬 값 (기본값: 1)
                ttl: 만료 시간(초) (선택 사항)
                prefix: 키 프리픽스 (기본값: "")
                
            Returns:
                증가 후 값 또는 None
            """
            if not self.redis_client:
                return None
                
            full_key = f"{prefix}:{key}" if prefix else key
            
            try:
                # 파이프라인으로 원자적 실행
                pipeline = self.redis_client.pipeline()
                pipeline.incrby(full_key, amount)
                
                # TTL 설정 (선택 사항)
                if ttl is not None:
                    pipeline.expire(full_key, ttl)
                    
                results = pipeline.execute()
                return results[0]  # incrby 결과
            except redis.RedisError as e:
                logger.error(f"캐시 증가 실패 - 키: {full_key}, 오류: {str(e)}")
                return None

    def decrement(self, key: str, amount: int = 1, ttl: Optional[int] = None, prefix: str = "") -> Optional[int]:
            """
            캐시 값 감소
            
            Args:
                key: 캐시 키
                amount: 감소시킬 값 (기본값: 1)
                ttl: 만료 시간(초) (선택 사항)
                prefix: 키 프리픽스 (기본값: "")
                
            Returns:
                감소 후 값 또는 None
            """
            if not self.redis_client:
                return None
                
            full_key = f"{prefix}:{key}" if prefix else key
            
            try:
                # 파이프라인으로 원자적 실행
                pipeline = self.redis_client.pipeline()
                pipeline.decrby(full_key, amount)
                
                # TTL 설정 (선택 사항)
                if ttl is not None:
                    pipeline.expire(full_key, ttl)
                    
                results = pipeline.execute()
                return results[0]  # decrby 결과
            except redis.RedisError as e:
                logger.error(f"캐시 감소 실패 - 키: {full_key}, 오류: {str(e)}")
                return None
        
    def clear_prefix(self, prefix: str) -> bool:
            """
            특정 프리픽스를 가진 모든 키 삭제
            
            Args:
                prefix: 키 프리픽스
                
            Returns:
                성공 여부
            """
            if not self.redis_client:
                return False
                
            try:
                # 프리픽스로 시작하는 모든 키 찾기
                keys = self.redis_client.keys(f"{prefix}:*")
                
                if not keys:
                    return True
                
                # 모든 키 삭제
                return bool(self.redis_client.delete(*keys))
            except redis.RedisError as e:
                logger.error(f"프리픽스 삭제 실패 - 프리픽스: {prefix}, 오류: {str(e)}")
                return False
        
    def set_add(self, key: str, *values, ttl: Optional[int] = None, prefix: str = "") -> bool:
            """
            Set에 값 추가
            
            Args:
                key: Set 키
                values: 추가할 값들
                ttl: 만료 시간(초) (선택 사항)
                prefix: 키 프리픽스 (기본값: "")
                
            Returns:
                성공 여부
            """
            if not self.redis_client or not values:
                return False
                
            full_key = f"{prefix}:{key}" if prefix else key
            
            try:
                # 파이프라인으로 원자적 실행
                pipeline = self.redis_client.pipeline()
                pipeline.sadd(full_key, *values)
                
                # TTL 설정 (선택 사항)
                if ttl is not None:
                    pipeline.expire(full_key, ttl)
                    
                pipeline.execute()
                return True
            except redis.RedisError as e:
                logger.error(f"Set 추가 실패 - 키: {full_key}, 오류: {str(e)}")
                return False
        
    def set_remove(self, key: str, *values, prefix: str = "") -> bool:
            """
            Set에서 값 제거
            
            Args:
                key: Set 키
                values: 제거할 값들
                prefix: 키 프리픽스 (기본값: "")
                
            Returns:
                성공 여부
            """
            if not self.redis_client or not values:
                return False
                
            full_key = f"{prefix}:{key}" if prefix else key
            
            try:
                return bool(self.redis_client.srem(full_key, *values))
            except redis.RedisError as e:
                logger.error(f"Set 제거 실패 - 키: {full_key}, 오류: {str(e)}")
                return False
        
    def set_members(self, key: str, prefix: str = "") -> List[str]:
            """
            Set의 모든 멤버 조회
            
            Args:
                key: Set 키
                prefix: 키 프리픽스 (기본값: "")
                
            Returns:
                Set 멤버 목록
            """
            if not self.redis_client:
                return []
                
            full_key = f"{prefix}:{key}" if prefix else key
            
            try:
                return list(self.redis_client.smembers(full_key))
            except redis.RedisError as e:
                logger.error(f"Set 멤버 조회 실패 - 키: {full_key}, 오류: {str(e)}")
                return []
        
    def set_is_member(self, key: str, value: str, prefix: str = "") -> bool:
            """
            값이 Set의 멤버인지 확인
            
            Args:
                key: Set 키
                value: 확인할 값
                prefix: 키 프리픽스 (기본값: "")
                
            Returns:
                멤버 여부
            """
            if not self.redis_client:
                return False
                
            full_key = f"{prefix}:{key}" if prefix else key
            
            try:
                return bool(self.redis_client.sismember(full_key, value))
            except redis.RedisError as e:
                logger.error(f"Set 멤버 확인 실패 - 키: {full_key}, 오류: {str(e)}")
                return False

    # 데코레이터: 함수 결과를 캐싱
    def cached(prefix: str = "", ttl: int = 300, key_builder: Optional[Callable] = None):
        """
        함수 결과를 캐싱하는 데코레이터
        
        Args:
            prefix: 캐시 키 프리픽스
            ttl: 캐시 유효 시간(초)
            key_builder: 캐시 키 생성 함수 (None인 경우 자동 생성)
            
        Returns:
            데코레이터 함수
        """
        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                # 캐시 서비스 인스턴스 가져오기
                cache_service = CacheService()
                
                # 캐시 키 생성
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    # 기본 키 생성: 함수명 + 인자 해시
                    args_str = ":".join(str(arg) for arg in args)
                    kwargs_str = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                    cache_key = f"{func.__name__}:{hash(args_str + kwargs_str)}"
                
                # 캐시에서 조회
                cached_result = cache_service.get_json(cache_key, prefix)
                if cached_result is not None:
                    return cached_result
                
                # 캐시 없으면 함수 실행
                result = await func(*args, **kwargs)
                
                # 결과 캐싱
                cache_service.set_json(cache_key, result, ttl, prefix)
                
                return result
            
            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                # 캐시 서비스 인스턴스 가져오기
                cache_service = CacheService()
                
                # 캐시 키 생성
                if key_builder:
                    cache_key = key_builder(*args, **kwargs)
                else:
                    # 기본 키 생성: 함수명 + 인자 해시
                    args_str = ":".join(str(arg) for arg in args)
                    kwargs_str = ":".join(f"{k}={v}" for k, v in sorted(kwargs.items()))
                    cache_key = f"{func.__name__}:{hash(args_str + kwargs_str)}"
                
                # 캐시에서 조회
                cached_result = cache_service.get_json(cache_key, prefix)
                if cached_result is not None:
                    return cached_result
                
                # 캐시 없으면 함수 실행
                result = func(*args, **kwargs)
                
                # 결과 캐싱
                cache_service.set_json(cache_key, result, ttl, prefix)
                
                return result
            
            # async 함수인지 여부에 따라 적절한 래퍼 반환
            if asyncio.iscoroutinefunction(func):
                return async_wrapper
            return sync_wrapper
        
        return decorator        
