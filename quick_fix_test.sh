#!/bin/bash
# quick_fix_test.sh - 빠른 수정 및 개별 테스트

echo "🔧 WebSocket 기능별 개별 테스트..."

# 1. QA 단독 테스트
echo "🧪 QA 기능 단독 테스트..."
cat > qa_test.py << 'EOF'
import asyncio
import websockets
import json
from datetime import datetime

async def test_qa_only():
    uri = "ws://localhost:8000/api/v1/ws/chat/qa_only_user"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ QA 테스트 연결 성공")
            
            # 간단한 QA 질문
            message = {
                "type": "user_message",
                "session_id": None,
                "data": {"message": "AES 암호화 알고리즘의 특징을 간단히 설명해주세요"},
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send(json.dumps(message, ensure_ascii=False))
            print("📤 QA 질문 전송")
            
            # 응답 수신
            response_count = 0
            while response_count < 5:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=20)
                    data = json.loads(response)
                    msg_type = data.get("type")
                    
                    print(f"📥 응답 {response_count + 1}: {msg_type}")
                    
                    if msg_type == "ai_response":
                        message = data["data"]["message"]
                        print(f"🤖 AI 응답: {message[:150]}...")
                        print("✅ QA 테스트 성공!")
                        return True
                    elif msg_type == "error":
                        print(f"❌ 오류: {data['data']['message']}")
                        return False
                    elif msg_type == "status_update":
                        status = data["data"]["message"]
                        print(f"⏳ 상태: {status}")
                    
                    response_count += 1
                    
                except asyncio.TimeoutError:
                    print("⏰ 응답 시간 초과")
                    return False
                    
    except Exception as e:
        print(f"❌ QA 테스트 실패: {e}")
        return False

if __name__ == "__main__":
    result = asyncio.run(test_qa_only())
    print(f"QA 테스트 결과: {'성공' if result else '실패'}")
EOF

python qa_test.py

echo ""
echo "🔧 문제 해결을 위한 로그 확인..."

# 2. API 서버 로그 확인
echo "📋 최근 API 서버 로그 (마지막 20줄):"
docker logs ai_agent_api_dev --tail 20

echo ""
echo "🔍 Redis 연결 상태 확인:"
docker exec ai_agent_redis redis-cli ping

echo ""
echo "💡 문제 해결 방안:"
echo "1. 타임아웃 증가 - 현재 15초 → 30초로 변경"
echo "2. 목적 판단 로직 확인 - LLM 응답 파싱 문제 가능성"
echo "3. 에러 처리 강화 - 구체적인 오류 메시지 확인"

# 3. 간단한 연결 테스트
echo ""
echo "🌐 기본 연결 테스트..."
cat > simple_connection_test.py << 'EOF'
import asyncio
import websockets
import json

async def simple_connection():
    try:
        async with websockets.connect("ws://localhost:8000/api/v1/ws/chat/simple_user") as ws:
            print("✅ 기본 연결 성공")
            
            # 핑 메시지
            ping_msg = {
                "type": "ping",
                "session_id": None,
                "data": {},
                "timestamp": "2025-05-26T10:00:00Z"
            }
            
            await ws.send(json.dumps(ping_msg))
            print("📤 핑 전송")
            
            response = await asyncio.wait_for(ws.recv(), timeout=5)
            data = json.loads(response)
            
            if data.get("type") == "pong":
                print("✅ 핑-퐁 성공")
                return True
            else:
                print(f"📥 응답: {data.get('type')}")
                return True
                
    except Exception as e:
        print(f"❌ 기본 연결 실패: {e}")
        return False

asyncio.run(simple_connection())
EOF

python simple_connection_test.py

# 정리
rm -f qa_test.py simple_connection_test.py

echo ""
echo "🎯 권장 다음 단계:"
echo "1. API 서버 재시작: docker restart ai_agent_api_dev"
echo "2. 개별 QA 테스트: python qa_test.py"
echo "3. 로그 모니터링: docker logs -f ai_agent_api_dev"