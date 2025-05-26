#!/bin/bash

echo "🔍 Planova 서비스 진단 및 복구 스크립트"
echo "======================================"

# 1. 컨테이너 상태 확인
echo "📦 Docker 컨테이너 상태 확인"
docker ps -a

echo -e "\n🌐 포트 확인"
netstat -tlnp | grep -E ':(80|443|8000)'

echo -e "\n📂 static 폴더 확인"
ls -la static/
echo "index.html 존재 여부:"
ls -la static/index.html 2>/dev/null && echo "✅ 존재" || echo "❌ 없음"

echo -e "\n📂 assets 폴더 확인"
ls -la static/assets/ 2>/dev/null && echo "✅ assets 폴더 존재" || echo "❌ assets 폴더 없음"

echo -e "\n🔒 SSL 인증서 확인"
ls -la ssl/ 2>/dev/null && echo "✅ SSL 폴더 존재" || echo "❌ SSL 폴더 없음"

echo -e "\n📝 Nginx 로그 확인 (최근 10줄)"
docker logs ai_agent_nginx --tail 10

echo -e "\n📝 API 로그 확인 (최근 10줄)"
docker logs ai_agent_api_dev --tail 10

echo -e "\n🔧 복구 시작"
echo "1. 컨테이너 재시작"
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d

echo -e "\n2. 서비스 연결 테스트"
sleep 10

echo "내부 API 테스트:"
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/health

echo -e "\n외부 HTTPS 테스트:"
curl -s -o /dev/null -w "%{http_code}" https://api.planova.kr/api/health

echo -e "\n✅ 진단 완료"