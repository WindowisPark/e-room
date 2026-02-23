# Frontend

새 프론트엔드 프로젝트 위치.

## 빌드 후 배포

```bash
# 의존성 설치
npm install

# 프로덕션 빌드 (결과물 → ./dist/)
npm run build
```

빌드 결과물(`dist/`)이 존재하면 서버가 `/static` 경로로 자동 서빙합니다.

## 환경변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `STATIC_DIR` | `./frontend/dist` | 빌드 결과물 경로 |
