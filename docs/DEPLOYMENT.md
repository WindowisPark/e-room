# Railway 배포 가이드

## 아키텍처

```
Railway Project: planova
├── Service: api          (FastAPI, Dockerfile)   ~$5-10/월
│   └── Volume: /app/storage                      ~$0.5/월
├── Database: PostgreSQL  (Railway managed)        ~$5/월
└── Service: Redis        (Railway managed)        ~$2/월
                                                  ─────────
                                                  ~$12-17/월

프론트엔드 → Cloudflare Pages  (무료)
파일 저장  → Cloudflare R2     (무료 10GB)
```

---

## 최초 배포 절차

### 1. Railway 프로젝트 생성

1. [railway.app](https://railway.app) 로그인
2. **New Project** → **Deploy from GitHub repo** → 이 저장소 선택
3. 자동으로 `Dockerfile` 감지하여 빌드

### 2. PostgreSQL 추가

Railway 대시보드 → **+ New Service** → **Database** → **PostgreSQL**

생성 후 `DATABASE_URL` 값을 복사.

### 3. Redis 추가

Railway 대시보드 → **+ New Service** → **Database** → **Redis**

생성 후 `REDIS_URL` 값을 복사.

### 4. 환경변수 설정

api 서비스 → **Variables** 탭에서 `.env.example` 항목 입력.

Railway managed service 변수는 참조 형식으로 연결:
```
DATABASE_URL  = ${{Postgres.DATABASE_URL}}
REDIS_URL     = ${{Redis.REDIS_URL}}
```

필수 입력 항목:
```
SECRET_KEY            = <python -c "import secrets; print(secrets.token_hex(32))">
ACCESS_SECRET_KEY     = <위와 동일 방법으로 생성>
REFRESH_SECRET_KEY    = <위와 동일 방법으로 생성>
POSTGRES_PASSWORD     = <Railway PostgreSQL 비밀번호>
AI_API_KEY            = sk-...
ENVIRONMENT           = production
FRONTEND_URL          = https://planova.kr
```

### 5. Persistent Volume 연결

api 서비스 → **Volumes** → **+ Add Volume**
- Mount Path: `/app/storage`
- 용량: 5GB (ChromaDB + 업로드 파일)

### 6. 커스텀 도메인

api 서비스 → **Settings** → **Custom Domain** → `api.planova.kr` 입력

Railway가 제공하는 CNAME을 DNS에 등록하면 자동 SSL 발급.

---

## Cloudflare R2 설정 (파일 저장소)

1. [Cloudflare 대시보드](https://dash.cloudflare.com) → **R2** → **Create bucket**
2. 버킷명: `planova-storage`
3. **Manage R2 API tokens** → Create token (Object Read & Write)
4. Railway 환경변수에 추가:
```
R2_ENABLED      = true
R2_BUCKET_NAME  = planova-storage
R2_ENDPOINT_URL = https://<account_id>.r2.cloudflarestorage.com
R2_ACCESS_KEY   = <token_access_key>
R2_SECRET_KEY   = <token_secret_key>
```

R2는 boto3의 S3 API와 호환됨. 기존 S3 코드에 `endpoint_url` 파라미터 추가로 사용 가능:
```python
s3 = boto3.client(
    "s3",
    endpoint_url=settings.R2_ENDPOINT_URL,
    aws_access_key_id=settings.R2_ACCESS_KEY,
    aws_secret_access_key=settings.R2_SECRET_KEY,
    region_name="auto",
)
```

---

## Cloudflare Pages (프론트엔드)

1. Cloudflare 대시보드 → **Pages** → **Connect to Git** → `planova_web` 저장소 선택
2. 빌드 설정:
   - Framework: `Vue (Vite)`
   - Build command: `npm run build`
   - Build output: `dist`
3. 환경변수:
   ```
   VITE_API_BASE_URL = https://api.planova.kr
   ```
4. 배포 후 커스텀 도메인 `planova.kr` 연결

---

## CI/CD 흐름

```
git push main
    ↓
Railway 자동 감지 (GitHub 연동)
    ↓
Docker 빌드 (~5분, 첫 빌드)
    ↓
entrypoint.sh 실행:
    1. alembic upgrade head  (DB 마이그레이션)
    2. gunicorn 시작
```

Railway는 무중단 배포(rolling deploy)를 지원함.
헬스체크(`/api/health`)가 통과해야 구버전 컨테이너가 종료됨.

---

## 로컬 개발

```bash
# .env.example → .env 복사 후 로컬 값 입력
cp .env.example .env

# Docker Compose로 로컬 실행
docker-compose -f docker-compose.dev.yml up
```

---

## 예상 비용 (월)

| 항목 | 비용 |
|------|------|
| Railway Hobby Plan | $5 |
| API 서비스 (1GB RAM) | ~$5 |
| PostgreSQL | ~$5 |
| Redis | ~$2 |
| Volume 5GB | ~$1.25 |
| Cloudflare R2 (10GB 무료) | $0 |
| Cloudflare Pages | $0 |
| **합계** | **~$18/월** |
