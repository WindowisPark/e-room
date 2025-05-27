# quick_test.py  
"""
빠른 기능 테스트용
"""

import asyncio
import websockets
import json

async def quick_qa_test():
    """QA 기능 빠른 테스트"""
    uri = "ws://localhost:8000/api/v1/ws/improved-chat/123"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ 연결 성공")
            
            # QA 질문 전송
            message = {
                "type": "user_message",
                "data": {"message": "안녕하세요"}
            }
            
            await websocket.send(json.dumps(message))
            print("📤 메시지 전송됨")
            
            # 응답 대기 (최대 10초)
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            data = json.loads(response)
            
            print(f"📥 응답 타입: {data.get('type')}")
            print(f"📝 응답 내용: {data.get('data', {}).get('message', 'No message')}")
            
    except asyncio.TimeoutError:
        print("⏰ 응답 타임아웃")
    except Exception as e:
        print(f"❌ 오류: {str(e)}")

async def quick_summary_test():
    """Summary 기능 빠른 테스트"""
    uri = "ws://localhost:8000/api/v1/ws/improved-chat/123"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ 연결 성공")
            
            # Summary 요청
            message = {
                "type": "user_message", 
                "data": {"message": "요약해줘"}
            }
            
            await websocket.send(json.dumps(message))
            print("📤 요약 요청 전송됨")
            
            # 파일 선택 요청 대기
            response = await asyncio.wait_for(websocket.recv(), timeout=10.0)
            data = json.loads(response)
            
            print(f"📥 응답 타입: {data.get('type')}")
            if data.get('type') == 'file_request':
                print("✅ 파일 선택 요청 받음")
                print(f"메시지: {data.get('data', {}).get('message')}")
                print(f"파일 수: {len(data.get('data', {}).get('available_files', []))}")
            
    except Exception as e:
        print(f"❌ 오류: {str(e)}")

if __name__ == "__main__":
    print("🧪 빠른 테스트 실행")
    print("\n1. QA 테스트:")
    asyncio.run(quick_qa_test())
    
    print("\n2. Summary 테스트:")
    asyncio.run(quick_summary_test())