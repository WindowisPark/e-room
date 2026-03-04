# Refactoring Log

> 운영 종료 후 재기동을 위한 리팩토링 작업 기록 | 시작일: 2026-02-23

---

## 이슈 목록

| # | 문제 | 심각도 | 상태 |
|---|------|--------|------|
| 1 | 운영보수 작업 부재 (헬스체크, lifespan 훅, 잔여 스크립트 정리) | 🟠 높음 | ✅ 완료 |
| 2 | 보안 문제 (하드코딩 시크릿, 세션 누수, 웹훅 미검증) | 🔴 긴급 | ✅ 완료 |
| 3 | 응답 속도 (커넥션 풀, 클라이언트 싱글톤, Redis 캐싱) | 🟠 높음 | ✅ 완료 |
| 4 | 동시 요청 시 API 먹통 (async 내 sync 블로킹 호출) | 🔴 긴급 | ✅ 완료 |
| 5 | [FE] 사용자 정보 하드코딩 + 401 localStorage 키 버그 | 🔴 긴급 | ✅ 완료 |
| 6 | [FE] 출석체크 API 미연동 (localStorage만 사용) | 🟠 높음 | ✅ 완료 |
| 7 | [FE] 콘솔에 카카오 키·토큰·사용자 정보 노출 | 🔴 긴급 | ✅ 완료 |
| 8 | [FE] 마이룸 카운트 하드코딩 | 🟡 보통 | ✅ 완료 |
| 9 | [FE] npm 의존성 보안 취약점 22건 | 🔴 긴급 | ✅ 완료 |
| 10 | [FE] 마이룸 카운트 API 미연동 (quizCount, summaryCount) | 🟡 보통 | ✅ 완료 |
| 11 | [FE] 카카오 로그인 authStore 미연동 (localStorage 직접 저장) | 🟠 높음 | ✅ 완료 |
| 12 | [BE] 캘린더 CRUD API 부재 | 🟡 보통 | ✅ 완료 |

---

## Phase 1 — 백엔드 안정화 (2026-02-23)

| 이슈 | 주요 변경 |
|------|----------|
| #1 운영보수 | `lifespan` 기동/종료 훅 추가, 잔여 스크립트 13개 삭제 |
| #2 보안 | 시크릿 기본값 제거(미설정 시 기동 거부), DB 세션 누수 수정, S3 버킷명 env화 |
| #3 속도 | 커넥션 풀(`pool_size=10, max_overflow=20`), OpenAI 싱글톤, `/ask` Redis 캐싱(TTL 1h) |
| #4 블로킹 | `graph.invoke()` 등 sync 호출 7곳 → `asyncio.to_thread()` 적용 |

---

## Phase 2 — 프론트엔드 정리 (2026-03-03)

| 이슈 | 주요 변경 |
|------|----------|
| #5 하드코딩 | `StudentHeader.vue` authStore 연동, `api/index.js` 401 키 버그(`'token'`→`'auth'`) 수정 |
| #6 출석 | `onMounted` / `checkAttendance()` → `memberAttendanceApi` 호출, localStorage fallback 유지 |
| #7 콘솔 | `LoginPage.vue`, `SignUpPage.vue` 민감 `console.log` 전체 제거 |
| #8 카운트 | 마이룸 하드코딩 수치 → `ref(0)` 변수화 |
| #9 취약점 | `pdfjs-dist` v3→v5, `axios`/`rollup`/`vite` 등 22건 패치 |

---

## v2 리팩토링 (2026-03-04)

**목표:** v1 종합 플랫폼 → "학습 + 취준" 슬림 플랫폼 (무료화)

### 제거된 기능

- **BE 엔드포인트**: teams, gamification, badges, events, attendance, payments, phone_verification, notifications, question
- **BE 서비스/모델**: team, gamification, payment, event, attendance, notification, question 관련 전체
- **FE**: board 라우터/페이지 4개, EventPage, TeamFileManager, boardApi.js, memberAttendanceApi.js
- **user 필드 제거**: `plan_type`, `points`, `level`, `exp`, `streak_days`, `phone_number` 등

### 버그 수정

- `cover_letter.py`, `job_research.py` sync → `asyncio.to_thread` 전환
- `main.py` `/api/debug/frontend` 보안 노출 엔드포인트 제거
- `exportPdf()` `window.open()` → axios + Blob (JWT 인증 포함)

### 사이드바 구조

```
홈 / 학습(PDF·AI튜터·캘린더) / 커리어(이력서·기업조사·자소서·마이룸)
```

### Alembic 마이그레이션

- `b1v2cleanup001`: 팀/게이미피케이션/결제 등 테이블 DROP, 경력 관리 테이블 CREATE

---

## Phase 3 — 미연동 이슈 해결 (2026-03-04)

| 이슈 | 주요 변경 |
|------|----------|
| #11 카카오 | `POST /auth/kakao/token` 신규 (SDK access_token → JWT 교환); `LoginPage.vue` authStore.setAuth() 연동 |
| #10 마이룸 | teamspaceCount 카드 제거; `onMounted`에서 `/users/me/details` 호출 → summaryCount/quizCount 연동 |
| #12 캘린더 | `CalendarTask`/`CalendarGoal` 모델·스키마·엔드포인트 신규; `StudentCalendarPage.vue` Composition API 재작성 + API 연동; Alembic `3eb97a66c727` |

---

## 변경 이력

| 날짜 | 작업 |
|------|------|
| 2026-02-23 | Phase 1: 백엔드 안정화 (#1~#4) |
| 2026-03-03 | Phase 2: 프론트엔드 정리 (#5~#9) |
| 2026-03-04 | v2 리팩토링: 팀/게이미피케이션/결제 전면 제거, 경력 관리 추가 |
| 2026-03-04 | Phase 3: 카카오 연동·마이룸·캘린더 CRUD (#10~#12) |
