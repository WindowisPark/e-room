# e-room v2 아키텍처

> 작성일: 2026-03-04

---

## 개요

**v1**: 팀협업, 게이미피케이션, 게시판, 결제, 출석 등 종합 플랫폼
**v2**: "학창시절 공부 → 취준" 두 단계 여정에 집중하는 슬림 플랫폼 (무료)

---

## 시스템 구성

```
[클라이언트: Vue 3 SPA]
      │
      │ HTTPS / REST API
      ▼
[FastAPI 서버]
  ├── JWT 인증 (Access/Refresh Token)
  ├── 카카오 OAuth
  ├── PDF 업로드/관리 → S3/R2
  ├── PDF AI 처리 → LangGraph + Gemini 2.5 Flash
  ├── 이력서/자소서/기업조사 CRUD
  └── WebSocket (AI 스트리밍 예정)
      │
      ├── PostgreSQL (메인 DB)
      ├── Redis (Refresh Token + AI 응답 캐시)
      └── ChromaDB (PDF 벡터 임베딩)
```

---

## Backend API 구조

```
/api/v1/
├── /auth            — 로그인, 회원가입, 카카오 OAuth, 토큰 갱신
├── /users           — 사용자 정보 CRUD
├── /pdf             — PDF 업로드/목록/삭제 (pdf_manager)
├── /pdf-agent       — AI 요약/문제생성/QA (LangGraph)
├── /tags            — PDF 메모/주석
├── /resume          — 이력서 프로필 + 항목 CRUD + JSON/PDF 내보내기
├── /jobs            — 채용공고 URL 스크래핑 + Gemini 분석 + 저장
├── /coverletter     — 자소서 CRUD + AI 초안 생성
└── /admin           — 사용자 관리 (관리자 전용)
```

---

## Frontend 라우터 구조

```
/                    → HomePage
/auth/login          → LoginPage
/auth/signup         → SignUpPage
/student/main        → StudentMainPage (대시보드)
/student/pdf         → StudentPdfPage (PDF 파일 관리)
/student/pdf/view/:id → PdfViewer (PDF 뷰어)
/student/aitutor     → StudentAiTutorPage
/student/calendar    → StudentCalendarPage
/student/resume      → StudentResumePage
/student/jobs        → StudentJobResearchPage
/student/coverletter → StudentCoverLetterPage
/student/myroom      → StudentMyroomPage
/student/support     → StudentSupportPage
```

---

## 사이드바 구조

```
┌─────────────────┐
│  [로고]          │
├─────────────────┤
│  홈              │
├─── 학습 ─────────┤
│  PDF 학습        │
│  AI 튜터         │
│  캘린더          │
├─── 커리어 ────────┤
│  이력서          │
│  기업 조사       │
│  자소서          │
├─────────────────┤
│  마이룸          │
│  고객지원        │
└─────────────────┘
```

---

## PDF AI 파이프라인 (LangGraph)

```
PDF 업로드
    │
    ▼
[ChromaDB 인제스트]
  ├── 텍스트 추출 (PyMuPDF)
  ├── 청크 분할
  └── 벡터 임베딩 → ChromaDB 저장
          │
          ├─ /pdf-agent/process   → 요약 생성 (summary_graph)
          ├─ /pdf-agent/ask       → QA 응답 (qa_graph) [Redis 캐시]
          ├─ /pdf-agent/exam      → 문제 생성 (exam_graph)
          └─ /pdf-agent/schedule  → 학습 일정 (schedule_graph)
```

---

## 데이터 모델

### 유지 모델

| 모델 | 테이블 | 설명 |
|------|--------|------|
| User | users | 사용자 (OAuth 포함) |
| PasswordResetToken | password_reset_tokens | 이메일 비번 재설정 |
| PDFFile | pdf_files | PDF 파일 메타데이터 |
| PDFTag | tags | PDF 메모/주석 |
| ResumeProfile | resume_profiles | 이력서 프로필 |
| ResumeItem | resume_items | 이력서 항목 |
| SavedCompany | saved_companies | 채용공고 저장 |
| CoverLetter | cover_letters | 자소서 |
| CoverLetterItem | cover_letter_items | 자소서 문항 |

### 제거 모델

Team, TeamMember, TeamActivity, PointHistory, Badge, UserBadge, Payment, Event, UserEvent, InviteCode, Attendance, Notification, Question

---

## 인증 흐름

```
이메일 로그인:
  POST /auth/login → { access_token, refresh_token }
  → access_token: Authorization 헤더
  → refresh_token: Redis 저장 (7일)
  → POST /auth/refresh-token → 새 access_token 발급

카카오 OAuth:
  GET /auth/kakao/authorize → 카카오 인증 페이지
  GET /auth/kakao/callback?code=... → JWT 발급
```

---

## 기술 스택

| 영역 | 기술 |
|------|------|
| Backend | FastAPI, SQLAlchemy, Alembic |
| AI | LangGraph, Gemini 2.5 Flash (`gemini-2.5-flash-preview-04-17`) |
| Vector DB | ChromaDB |
| Cache | Redis (Refresh Token + AI 캐시) |
| Storage | AWS S3 / Cloudflare R2 |
| Frontend | Vue 3, Vite, Vue Router |
| Auth | JWT (PyJWT) + 카카오 OAuth |
| Deploy | Railway (API + Redis + PostgreSQL) + Cloudflare Pages (FE) |
