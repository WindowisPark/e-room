창의학기제 VUE || FLUTTER || FASTAPI 

# 📚  e-room : PDF 협업 플랫폼

PDF 문서에 주석을 달고 팀 단위로 협업하며 학습할 수 있는 웹 애플리케이션입니다.

## 🌟 주요 기능

- **📄 PDF 관리**: PDF 업로드, 조회, 삭제, 이름 변경 기능
- **✏️ 주석 기능**: PDF에 하이라이트, 노트, 밑줄 등 다양한 주석 추가
- **👥 팀 협업**: 팀스페이스 생성 및 관리, 멤버 초대, 실시간 협업
- **🔄 실시간 동기화**: WebSocket을 통한 실시간 주석 및 커서 위치 공유
- **🚀 게이미피케이션**: 포인트, 레벨, 배지 시스템으로 사용자 참여 유도
- **🔔 알림 시스템**: 멘션, 팀 초대 등 다양한 이벤트 알림
- **💰 구독 서비스**: 프리미엄/VIP 요금제를 통한 추가 기능 제공
- **📱 전화번호 인증**: SMS를 통한 사용자 전화번호 인증

## 🔧 기술 스택

### 백엔드
- **언어 및 프레임워크**: Python, FastAPI
- **데이터베이스**: PostgreSQL, Redis(캐싱, 실시간 메시징)
- **인증**: JWT, OAuth2(카카오 로그인)
- **결제 시스템**: 포트원(구 아임포트) 연동
- **파일 저장**: 로컬 파일 시스템(운영 환경에서는 S3 권장)

### 프론트엔드
- React.js 기반 SPA (프론트엔드 코드는 별도 저장소에 있음)

## 📂 프로젝트 구조

```
app/
├── api/                 # API 라우터
│   ├── deps.py          # 의존성 주입
│   └── v1/              # API 엔드포인트 (버전 1)
│       ├── endpoints/   # 기능별 엔드포인트
│       └── websocket/   # WebSocket 관련 기능
├── core/                # 핵심 기능 및 설정
│   ├── config.py        # 환경 설정
│   ├── security.py      # 인증 및 보안
│   └── redis_helper.py  # Redis 유틸리티
├── crud/                # 데이터베이스 CRUD 작업
├── db/                  # 데이터베이스 설정
├── models/              # SQLAlchemy 모델
├── schemas/             # Pydantic 스키마
└── services/            # 비즈니스 로직
```

## 🔐 주요 기능 설명

### 인증 시스템
- JWT 기반 인증
- 카카오 OAuth2 통합
- 액세스 토큰 및 리프레시 토큰 시스템

### 팀 스페이스
- 팀 생성 및 관리 (소유자, 편집자, 조회자 권한 구분)
- 팀 활동 로그 기록
- 실시간 협업 지원

### PDF 관리 및 주석
- PDF 업로드 및 관리
- 주석 생성, 수정, 삭제
- 주석 내 @멘션 및 #해시태그 지원

### 실시간 협업
- WebSocket을 통한 실시간 협업
- 커서 위치 공유
- 주석 실시간 동기화

### 게이미피케이션
- 포인트 시스템 (활동에 따른 포인트 적립)
- 레벨 시스템 (포인트에 따른 레벨업)
- 배지 시스템 (특정 달성 시 배지 획득)

### 결제 시스템
- 포트원(구 아임포트) 연동
- 구독 요금제 (프리미엄/VIP)
- 웹훅을 통한 결제 상태 동기화

## 🚀 설치 및 실행 방법

### 요구 사항
- Python 3.9 이상
- PostgreSQL
- Redis
- 포트원(구 아임포트) 계정 (결제 기능 사용 시)

### 환경 설정

1. 저장소 클론
```bash
git clone https://github.com/your-username/ai-agent.git
cd ai-agent
```

2. 가상 환경 설정
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

3. 의존성 설치
```bash
pip install -r requirements.txt
```

4. .env 파일 설정
```
# 데이터베이스 설정
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
POSTGRES_DB=ai_agent

# JWT 설정
ACCESS_SECRET_KEY=your_access_secret_key
REFRESH_SECRET_KEY=your_refresh_secret_key
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# 카카오 로그인 설정
KAKAO_CLIENT_ID=your_kakao_client_id
KAKAO_CLIENT_SECRET=your_kakao_client_secret
KAKAO_REDIRECT_URI=http://localhost:8000/api/v1/auth/kakao/callback

# Redis 설정
REDIS_HOST=localhost
REDIS_PORT=6379

# 포트원(아임포트) 설정
IAMPORT_API_KEY=your_iamport_api_key
IAMPORT_API_SECRET=your_iamport_api_secret
IAMPORT_MERCHANT_ID=your_iamport_merchant_id
```

5. 데이터베이스 마이그레이션
```bash
alembic upgrade head
```

6. 애플리케이션 실행
```bash
uvicorn app.main:app --reload
```

7. API 문서 확인
- Swagger UI: http://localhost:8000/api/v1/docs

## 🧪 테스트 실행

```bash
pytest
```

## 📄 API 문서

API 문서는 Swagger UI를 통해 확인할 수 있습니다:
- http://localhost:8000/api/v1/docs

## 🛠️ 개발 가이드

### 브랜치 전략
- `main`: 운영용 브랜치
- `dev`: 개발 브랜치
- `feature/*`: 기능 개발 브랜치

### 커밋 메시지 규칙
- `feat`: 새로운 기능 추가
- `fix`: 버그 수정
- `refactor`: 코드 리팩토링
- `docs`: 문서 수정
- `test`: 테스트 코드 추가/수정
- `chore`: 빌드 과정 또는 보조 도구 변경

### 코드 포맷팅
코드 일관성 유지를 위해 다음 도구 사용을 권장합니다:
- `black`: Python 코드 포맷팅
- `isort`: import 문 정렬

## 📝 라이선스

이 프로젝트는 MIT 라이선스를 따릅니다 - 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

## 👥 기여자

- [개발자 이름](https://github.com/WindowisPark)

## 📞 문의

질문이나 제안 사항이 있으시면 [이슈](https://github.com/WindowisPark/e-room/issues)를 등록해 주세요.
