import time
from collections import defaultdict, deque
from fastapi import HTTPException, Request, status


class RateLimiter:
    """IP 기반 in-memory sliding window rate limiter."""

    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque] = defaultdict(deque)

    def _clean(self, key: str, now: float):
        q = self._requests[key]
        while q and q[0] <= now - self.window_seconds:
            q.popleft()

    def check(self, key: str):
        now = time.time()
        self._clean(key, now)
        if len(self._requests[key]) >= self.max_requests:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="요청이 너무 많습니다. 잠시 후 다시 시도해주세요.",
            )
        self._requests[key].append(now)

    def reset(self):
        self._requests.clear()


# 사전 정의된 리미터 인스턴스
login_limiter = RateLimiter(max_requests=5, window_seconds=60)
register_limiter = RateLimiter(max_requests=3, window_seconds=60)
forgot_password_limiter = RateLimiter(max_requests=3, window_seconds=60)


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
