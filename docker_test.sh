#!/bin/bash
# docker_test.sh - 도커 환경에서 WebSocket 테스트

echo "🐳 도커 환경에서 WebSocket 테스트 시작..."

# 1. API 컨테이너에서 테스트 실행
echo "📦 API 컨테이너에 접속하여 테스트 실행..."

docker exec -it ai_agent_api_dev bash -c "
    echo '🔧 테스트 환경 설정...'
    
    # 테스트 의존성 설치
    pip install pytest pytest-asyncio pytest-mock pytest-cov httpx websockets
    
    # Redis 연결 확인 (도커 내부 네트워크 사용)
    echo '📡 Redis 연결 테스트...'
    python -c \"
import redis
try:
    r = redis.from_url('redis://redis:6379/0')
    result = r.ping()
    print(f'✅ Redis 연결 성공: {result}')
except Exception as e:
    print(f'❌ Redis 연결 실패: {e}')
\"
    
    # 환경 변수 설정
    export REDIS_URL='redis://redis:6379/0'
    export PYTHONPATH='/app'
    
    echo '🧪 테스트 실행 중...'
    
    # 테스트 파일 생성 (간단한 연결 테스트)
    cat > /tmp/test_docker_websocket.py << 'EOF'
import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

# 간단한 연결 테스트
def test_docker_environment():
    \"\"\"도커 환경 테스트\"\"\"
    import redis
    
    # Redis 연결 테스트
    r = redis.from_url('redis://redis:6379/0')
    assert r.ping() == True
    print('✅ Redis 연결 성공')
    
    # 환경 변수 확인
    import os
    assert os.getenv('REDIS_URL') == 'redis://redis:6379/0'
    print('✅ 환경 변수 설정 성공')

@pytest.mark.asyncio
async def test_websocket_import():
    \"\"\"WebSocket 모듈 임포트 테스트\"\"\"
    try:
        from app.services.session_manager import SessionManager
        from app.api.v1.websocket.chat import WebSocketManager
        print('✅ WebSocket 모듈 임포트 성공')
        
        # SessionManager 인스턴스 생성 테스트
        session_manager = SessionManager('redis://redis:6379/0')
        session_id = session_manager.create_session('test_user', 'qa')
        assert session_id.startswith('session:test_user:')
        print(f'✅ 세션 생성 성공: {session_id}')
        
        # 정리
        session_manager.cleanup_session(session_id)
        print('✅ 세션 정리 성공')
        
    except ImportError as e:
        pytest.fail(f'모듈 임포트 실패: {e}')
    except Exception as e:
        pytest.fail(f'테스트 실행 실패: {e}')

if __name__ == '__main__':
    test_docker_environment()
    asyncio.run(test_websocket_import())
    print('🎉 모든 테스트 통과!')
EOF
    
    # 테스트 실행
    cd /app
    python /tmp/test_docker_websocket.py
    
    echo '✅ 도커 환경 테스트 완료!'
"

echo "🌐 WebSocket 서버 연결 테스트..."

# 2. 외부에서 WebSocket 연결 테스트
cat > test_external_connection.py << 'EOF'
import asyncio
import websockets
import json
from datetime import datetime

async def test_external_websocket():
    """외부에서 도커 WebSocket 서버 연결 테스트"""
    uri = "ws://localhost:8000/api/v1/ws/chat/test_user"
    
    try:
        print(f"🔌 WebSocket 연결 시도: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket 연결 성공!")
            
            # 테스트 메시지 전송
            test_message = {
                "type": "user_message",
                "session_id": None,
                "data": {"message": "안녕하세요! 테스트 메시지입니다."},
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(test_message, ensure_ascii=False))
            print("📤 테스트 메시지 전송 완료")
            
            # 응답 대기 (최대 5초)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                data = json.loads(response)
                print(f"📥 응답 수신: {data.get('type', 'unknown')}")
                print("✅ WebSocket 통신 테스트 성공!")
                return True
                
            except asyncio.TimeoutError:
                print("⏰ 응답 대기 시간 초과 (5초)")
                return False
                
    except Exception as e:
        print(f"❌ WebSocket 연결 실패: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_external_websocket())
    if result:
        print("🎉 외부 연결 테스트 성공!")
    else:
        print("💥 외부 연결 테스트 실패!")
EOF

python test_external_connection.py

# 정리
rm -f test_external_connection.py

echo "🏁 도커 환경 테스트 완료!"