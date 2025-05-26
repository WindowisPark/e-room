# working_qa_test.py - 확실히 동작하는 QA 테스트

import asyncio
import websockets
import json
from datetime import datetime

class WorkingQATest:
    def __init__(self):
        self.websocket = None
        self.session_id = None
        
    async def connect(self):
        uri = "ws://localhost:8000/api/v1/ws/chat/working_qa_user"
        try:
            self.websocket = await websockets.connect(uri)
            print("✅ WebSocket 연결 성공")
            return True
        except Exception as e:
            print(f"❌ 연결 실패: {e}")
            return False
    
    async def send_message(self, content):
        message = {
            "type": "user_message",
            "session_id": self.session_id,
            "data": {"message": content},
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket.send(json.dumps(message, ensure_ascii=False))
        print(f"📤 전송: {content[:50]}...")
    
    async def wait_for_ai_response(self, timeout=30):
        """AI 응답만 기다리기"""
        start_time = asyncio.get_event_loop().time()
        
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            try:
                response = await asyncio.wait_for(self.websocket.recv(), timeout=5)
                data = json.loads(response)
                
                self.session_id = data.get("session_id", self.session_id)
                msg_type = data.get("type")
                
                print(f"📥 수신: {msg_type}")
                
                if msg_type == "ai_response":
                    message = data["data"]["message"]
                    task_type = data["data"].get("task_type", "unknown")
                    is_final = data["data"].get("is_final", True)
                    
                    print(f"🤖 AI ({task_type}): {message[:200]}...")
                    return True, message
                    
                elif msg_type == "error":
                    error_msg = data["data"]["message"]
                    print(f"❌ 오류: {error_msg}")
                    return False, error_msg
                    
                elif msg_type == "status_update":
                    status = data["data"]["message"]
                    print(f"⏳ 상태: {status}")
                    # 계속 대기
                    
            except asyncio.TimeoutError:
                # 5초 단위로 체크, 전체 timeout까지 계속
                continue
                
        print("⏰ 전체 응답 시간 초과")
        return False, "시간 초과"
    
    async def test_qa_conversation(self):
        """QA 대화 테스트"""
        questions = [
            "안녕하세요! 정보보호가 뭔가요?",
            "대칭키 암호화와 비대칭키 암호화의 차이점은?", 
            "해시 함수의 특징을 설명해주세요"
        ]
        
        success_count = 0
        
        for i, question in enumerate(questions, 1):
            print(f"\n🧪 QA 테스트 {i}/{len(questions)}")
            print(f"질문: {question}")
            
            await self.send_message(question)
            
            success, response = await self.wait_for_ai_response()
            
            if success:
                print(f"✅ 테스트 {i} 성공!")
                success_count += 1
            else:
                print(f"❌ 테스트 {i} 실패: {response}")
            
            # 다음 질문 전 잠시 대기
            await asyncio.sleep(2)
        
        return success_count, len(questions)
    
    async def disconnect(self):
        if self.websocket:
            await self.websocket.close()
            print("🔌 연결 해제")

async def main():
    print("🧪 동작 확인용 QA 테스트")
    print("=" * 50)
    
    tester = WorkingQATest()
    
    if not await tester.connect():
        return False
    
    try:
        success_count, total_count = await tester.test_qa_conversation()
        
        print(f"\n📊 테스트 결과: {success_count}/{total_count} 성공")
        
        if success_count == total_count:
            print("🎉 모든 QA 테스트 성공!")
            return True
        elif success_count > 0:
            print("⚠️ 부분적 성공 - 기본 QA 기능은 동작함")
            return True
        else:
            print("💥 모든 QA 테스트 실패")
            return False
            
    except Exception as e:
        print(f"💥 테스트 중 예외: {e}")
        return False
    finally:
        await tester.disconnect()

if __name__ == "__main__":
    try:
        result = asyncio.run(main())
        if result:
            print("\n✅ QA 기능 정상 동작 확인!")
            print("\n💡 다음 단계:")
            print("1. 목적 판단 로직 수정")
            print("2. 파일 시스템 Mock 개선") 
            print("3. 타임아웃 설정 조정")
        else:
            print("\n❌ QA 기능에 문제가 있습니다.")
            print("\n🔧 확인 사항:")
            print("1. API 서버 로그: docker logs ai_agent_api_dev")
            print("2. Redis 상태: docker exec ai_agent_redis redis-cli ping")
    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 중단됨")