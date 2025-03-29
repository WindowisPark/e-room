# docker/backend/Dockerfile

FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    gcc \
    netcat-traditional \
    postgresql-client \
    python3-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 파이썬 패키지 설치
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 프로젝트 패키지 설치 (editable 모드)
RUN pip install -e .

# entrypoint.sh 복사 및 실행 권한 부여
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# 포트 개방
EXPOSE 8000

# 컨테이너 시작 시 실행할 스크립트
ENTRYPOINT ["/app/entrypoint.sh"]
