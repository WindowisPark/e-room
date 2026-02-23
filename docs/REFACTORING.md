# Refactoring Log

> 운영 종료 후 재기동을 위한 리팩토링 작업 기록
> 시작일: 2026-02-23

---

## 식별된 문제 목록

| # | 문제 | 심각도 | 상태 |
|---|------|--------|------|
| 1 | 운영보수용 작업 부재 (헬스체크, 시작/종료 훅, 디버그 파일 잔존 등) | 🟠 높음 | ✅ 완료 |
| 2 | 보안 문제 (하드코딩 시크릿, 세션 누수, 웹훅 미검증 등) | 🔴 긴급 | ✅ 완료 |
| 3 | 응답 처리 속도 (커넥션 풀, 클라이언트 싱글톤, 캐싱 부재) | 🟠 높음 | ✅ 완료 |
| 4 | 동시 요청 시 API 먹통 (async 함수 내 sync 블로킹 호출) | 🔴 긴급 | ✅ 완료 |

---

## Issue #4 — 동시 요청 시 API 먹통

### 원인 분석

FastAPI는 `asyncio` 이벤트 루프 기반으로 동작한다.
`async def` 엔드포인트 내에서 **동기 블로킹 함수를 직접 호출**하면
해당 함수가 완료될 때까지 이벤트 루프 전체가 멈춰 다른 모든 요청이 대기 상태가 된다.

LangGraph의 `graph.invoke(state)`는 내부적으로 여러 LLM API 호출 + CPU 연산을 수행하는
무거운 **동기 함수**로, 수초~수십 초가 소요될 수 있다.

### 영향 받은 파일

| 파일 | 함수 | 블로킹 호출 |
|------|------|------------|
| `app/api/v1/endpoints/pdf_agent.py` | `process_document` | `graph.invoke(state)` |
| `app/api/v1/endpoints/pdf_agent.py` | `ask_question` | `judge_the_purpose_of_the_input()`, `graph.invoke(state)` |
| `app/api/v1/endpoints/pdf_agent.py` | `generate_exam_without_previous` | `graph.invoke(state)` |
| `app/api/v1/endpoints/pdf_agent.py` | `generate_schedule_without_doc` | `graph.invoke(state)` |
| `app/services/pdf_agent/ai_service.py` | `run_summary` | `graph.invoke(state)` |
| `app/services/pdf_agent/ai_service.py` | `run_question_generation` | `graph.invoke(state)` |
| `app/services/pdf_agent/ai_service.py` | `run_qa` | `graph.invoke(state)` |

### 해결책

`asyncio.to_thread()` (Python 3.9+)를 사용해 동기 함수를 별도 스레드에서 실행.
이벤트 루프를 블로킹하지 않으면서 결과를 await 할 수 있다.

```python
# Before (이벤트 루프 블로킹)
result = graph.invoke(state)

# After (스레드풀에서 실행, 이벤트 루프 비차단)
result = await asyncio.to_thread(graph.invoke, state)
```

### 변경 파일

- `app/api/v1/endpoints/pdf_agent.py` — 4곳 수정
- `app/services/pdf_agent/ai_service.py` — 3곳 수정

---

## Static Files — 새 프론트엔드 연결

### 기존 문제

`app/main.py`에 프론트엔드 경로가 Java Spring 경로로 하드코딩:
```python
STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Board_Backend", "src", "main", "webapp", "resources"))
```
해당 디렉토리가 없으면 **서버 시작 자체가 실패**했다.

### 변경 내용

- 경로를 환경변수 `STATIC_DIR` (기본값 `./frontend/dist`)로 대체
- 디렉토리가 없으면 mount를 건너뜀 (서버 정상 기동)
- `frontend/` 디렉토리 구조 생성 (추후 React/Vite 빌드 결과물 위치)

### 프론트엔드 배포 흐름 (예정)

```
frontend/          ← 새 프론트엔드 소스 (별도 관리)
  ├── src/
  ├── public/
  ├── package.json
  └── dist/        ← 빌드 결과물 (npm run build)
       └── ...     ← /static 으로 서빙됨
```

환경변수 설정:
```env
STATIC_DIR=./frontend/dist
```

---

## Issue #1 — 운영보수 작업

### 변경 내용

| 파일 | 수정 항목 |
|------|----------|
| `app/main.py` | `lifespan` 컨텍스트 매니저 추가 — 기동 시 DB 연결 검증, 종료 시 커넥션 풀 정리 |
| `app/debug_redis.py` | 삭제 |
| `app/db/base_models_fix.py` | 삭제 (`base_models.py`가 최신 버전) |
| `tatus`, `*.patch` | 루트 잔재 파일 삭제 |
| `app/scripts/` | test_*, simple_*, fix_*, patch_* 13개 스크립트 삭제 |

**유지한 스크립트**: `app/scripts/init_badges.py` — 초기 배지 데이터 세팅용

### lifespan 동작

```
서버 기동
 └─ DB SELECT 1 실행 → 실패 시 critical 로그 + 기동 중단
 └─ "서버 기동 완료" 로그

서버 종료
 └─ engine.dispose() → 커넥션 풀 전체 반환
 └─ "DB 커넥션 풀 정리 완료" 로그
```

---

## Issue #2 — 보안 문제

### 변경 내용

| 파일 | 수정 항목 |
|------|----------|
| `app/core/config.py` | `POSTGRES_PASSWORD`, `SECRET_KEY`, `ACCESS_SECRET_KEY`, `REFRESH_SECRET_KEY` 기본값 제거 → 필수값으로 변경 (미설정 시 앱 시작 거부) |
| `app/core/config.py` | `IAMPORT_WEBHOOK_SECRET: str = ""` → `Optional[str] = None` |
| `app/core/config.py` | 시작 시 `DATABASE_URI`(비번 포함) stdout 출력 제거 |
| `app/core/security.py` | WebSocket DB 세션 누수 수정: `next(get_db())` → `SessionLocal()` + `finally: db.close()` |
| `app/core/security.py` | `verify_iamport_webhook`: 시크릿 미설정 시 500, 서명 헤더 누락 시 403 반환 |
| `app/core/security.py` | 미사용 `REDIS_HOST`, `import os` 제거 |
| `app/api/deps.py` | `redis_client` 중복 import 제거 (두 번째 import가 첫 번째를 덮어쓰던 버그) |
| `app/api/v1/endpoints/pdf_agent.py` | S3 버킷명 하드코딩 제거 → `settings.S3_BUCKET_NAME` 사용 |

### .env 필수 항목 (미설정 시 앱 기동 불가)

```env
POSTGRES_PASSWORD=<your_db_password>
SECRET_KEY=<random_secret>
ACCESS_SECRET_KEY=<random_secret>
REFRESH_SECRET_KEY=<random_secret>
```

시크릿 키 생성:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Issue #3 — 응답 처리 속도

### 변경 내용

| 파일 | 수정 항목 |
|------|----------|
| `app/db/session.py` | `create_engine`에 `pool_size=10`, `max_overflow=20`, `pool_pre_ping=True`, `pool_recycle=1800` 추가 |
| `app/services/pdf_agent/ai_agent.py` | `AsyncOpenAI` 클라이언트 모듈 레벨 싱글톤 (`get_openai_client()`)으로 교체 — 매 호출마다 TCP 재연결 제거 |
| `app/api/v1/endpoints/pdf_agent.py` | `/ask` 엔드포인트에 Redis 캐싱 적용 — 동일 쿼리 재요청 시 LLM 호출 생략 (TTL 1시간) |

> `ChromaDBService`는 이미 `__new__` 싱글톤이 구현되어 있어 변경 불필요.

### 커넥션 풀 설정 근거

| 옵션 | 값 | 의미 |
|------|-----|------|
| `pool_size` | 10 | 상시 유지 커넥션 수 (기본값 5 → 2배) |
| `max_overflow` | 20 | 피크 시 최대 추가 커넥션 (총 30개) |
| `pool_pre_ping` | True | 사용 전 커넥션 유효성 검사 (stale connection 방지) |
| `pool_recycle` | 1800 | 30분마다 커넥션 재생성 (DB 타임아웃 방지) |

### 캐시 키 설계

```
ai_ask:{sha256(user_id:query)}   TTL=3600s
```
- 사용자별로 분리되어 다른 사용자의 응답과 섞이지 않음
- TTL 만료 후 자동 재처리

---

## 변경 이력

| 날짜 | 작업 | 담당 |
|------|------|------|
| 2026-02-23 | Issue #4 graph.invoke() 블로킹 수정 | Claude Code |
| 2026-02-23 | Static 파일 경로 수정 + 프론트엔드 구조 생성 | Claude Code |
| 2026-02-23 | Issue #2 보안 문제 수정 | Claude Code |
| 2026-02-23 | Issue #3 응답 속도 개선 | Claude Code |
| 2026-02-23 | Issue #1 운영보수 작업 | Claude Code |
