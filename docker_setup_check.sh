#!/bin/bash
# docker_setup_check.sh - 도커 환경 설정 점검

echo "🐳 도커 환경 설정 점검 시작..."

# 1. 컨테이너 상태 확인
echo "📦 컨테이너 상태 확인..."
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# 2. Nginx 컨테이너 문제 해결
echo ""
echo "🔧 Nginx 컨테이너 재시작 중..."
if docker ps -a | grep -q "ai_agent_nginx.*Restarting"; then
    echo "⚠️ Nginx 컨테이너가 재시작 루프에 있습니다. 수정 중..."
    
    # Nginx 컨테이너 중지 및 제거
    docker stop ai_agent_nginx 2>/dev/null
    docker rm ai_agent_nginx 2>/dev/null
    
    # Nginx 컨테이너 재시작 (SSL 없이)
    docker run -d \
        --name ai_agent_nginx \
        --network e-room_default \
        -p 80:80 \
        -v "$(pwd)/static:/usr/share/nginx/html" \
        nginx:alpine
    
    echo "✅ Nginx 컨테이너 재시작 완료"
else
    echo "✅ Nginx 컨테이너 상태 정상"
fi

# 3. API 서버 상태 확인
echo ""
echo "🌐 API 서버 상태 확인..."
if curl -s http://localhost:8000/docs > /dev/null; then
    echo "✅ API 서버 정상 작동 (http://localhost:8000)"
else
    echo "⚠️ API 서버 응답 없음. 로그 확인 중..."
    docker logs ai_agent_api_dev --tail 10
fi

# 4. Redis 연결 테스트
echo ""
echo "📡 Redis 연결 테스트..."
if docker exec ai_agent_redis redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis 서버 정상 작동"
else
    echo "❌ Redis 서버 연결 실패"
fi

# 5. PostgreSQL 연결 테스트
echo ""
echo "🗄️ PostgreSQL 연결 테스트..."
if docker exec ai_agent_postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo "✅ PostgreSQL 서버 정상 작동"
else
    echo "❌ PostgreSQL 서버 연결 실패"
fi

# 6. 네트워크 확인
echo ""
echo "🔌 도커 네트워크 확인..."
docker network ls | grep e-room

# 7. 포트 사용 현황
echo ""
echo "🚪 포트 사용 현황..."
echo "8000: API 서버"
echo "6380: Redis (외부 접근)"
echo "5433: PostgreSQL (외부 접근)"
echo "8081: Redis Commander"
if command -v netstat > /dev/null; then
    netstat -tlnp | grep -E ":(8000|6380|5433|8081)" 2>/dev/null | head -10
fi

# 8. WebSocket 테스트 준비
echo ""
echo "🧪 WebSocket 테스트 환경 준비..."

# 테스트 의존성 설치 (API 컨테이너 내부)
docker exec ai_agent_api_dev bash -c "
    pip install -q websockets pytest pytest-asyncio 2>/dev/null || echo '⚠️ 테스트 의존성 설치 필요'
"

# 9. 환경 변수 확인
echo ""
echo "🔧 환경 변수 확인..."
docker exec ai_agent_api_dev bash -c "
    echo 'REDIS_HOST: '$(echo \$REDIS_HOST)
    echo 'REDIS_PORT: '$(echo \$REDIS_PORT)
    echo 'POSTGRES_SERVER: '$(echo \$POSTGRES_SERVER)
"

# 10. 로그 확인
echo ""
echo "📋 최근 API 서버 로그..."
docker logs ai_agent_api_dev --tail 5

echo ""
echo "🎯 테스트 실행 준비 완료!"
echo ""
echo "다음 명령으로 테스트 실행:"
echo "1. 자동 테스트: ./docker_test.sh"
echo "2. 수동 테스트: python docker_manual_test.py"
echo "3. API 문서: http://localhost:8000/docs"
echo "4. Redis UI: http://localhost:8081"