# debug_schedule_test.py
"""
Schedule 기능 상세 디버깅 테스트
"""

import asyncio
import websockets
import json
import time

async def test_schedule_step_by_step():
    """스케줄러 단계별 테스트"""
    url = "ws://localhost:8000/api/v1/ws/improved-chat/123"
    
    try:
        async with websockets.connect(url) as websocket:
            print("✅ WebSocket 연결 성공")
            
            # 1. 스케줄 요청
            message = {
                "type": "user_message",
                "data": {"message": "학습 계획 짜줘"}
            }
            
            await websocket.send(json.dumps(message, ensure_ascii=False))
            print("📤 스케줄 요청 전송")
            
            # 2. 파일 선택 요청 대기
            response = await websocket.recv()
            data = json.loads(response)
            print(f"📥 응답: {data.get('type')} - {data.get('data', {}).get('message', '')}")
            
            if data.get("type") == "file_request":
                available_files = data.get("data", {}).get("available_files", [])
                print(f"📁 사용 가능한 파일: {len(available_files)}개")
                
                # 파일 선택 (가상의 파일 2개)
                file_selection = {
                    "type": "file_selection",
                    "data": {
                        "selected_files": [
                            "users/123/study/math.pdf",
                            "users/123/study/science.pdf"
                        ],
                        "skip": False
                    }
                }
                
                await websocket.send(json.dumps(file_selection))
                print("📤 파일 선택 전송")
                
                # 3. 중요도 입력 요청 대기
                response = await websocket.recv()
                data = json.loads(response)
                print(f"📥 응답: {data.get('type')}")
                print(f"📝 메시지: {data.get('data', {}).get('message', '')}")
                
                if data.get("type") == "ai_response":
                    input_required = data.get("data", {}).get("input_required")
                    if input_required == "importance":
                        print("✅ 중요도 입력 요청 수신")
                        
                        # 중요도 입력
                        importance_message = {
                            "type": "user_message",
                            "data": {"message": "math: 5, science: 4"}
                        }
                        
                        await websocket.send(json.dumps(importance_message, ensure_ascii=False))
                        print("📤 중요도 입력 전송")
                        
                        # 4. 마감일 입력 요청 대기
                        response = await websocket.recv()
                        data = json.loads(response)
                        print(f"📥 응답: {data.get('type')}")
                        print(f"📝 메시지: {data.get('data', {}).get('message', '')}")
                        
                        if data.get("type") == "ai_response":
                            input_required = data.get("data", {}).get("input_required")
                            if input_required in ["deadline", "deadlines"]:
                                print("✅ 마감일 입력 요청 수신")
                                
                                # 마감일 입력
                                deadline_message = {
                                    "type": "user_message",
                                    "data": {"message": "math: 2025-06-01, science: 2025-06-03"}
                                }
                                
                                await websocket.send(json.dumps(deadline_message, ensure_ascii=False))
                                print("📤 마감일 입력 전송")
                                
                                # 5. 처리 과정 및 결과 모니터링
                                print("\n⏳ 스케줄 생성 과정 모니터링...")
                                
                                max_wait = 60  # 60초 대기
                                start_time = time.time()
                                
                                while time.time() - start_time < max_wait:
                                    try:
                                        response = await asyncio.wait_for(websocket.recv(), timeout=10)
                                        data = json.loads(response)
                                        response_type = data.get("type")
                                        
                                        print(f"📥 응답: {response_type}")
                                        
                                        if response_type == "status_update":
                                            message = data.get("data", {}).get("message", "")
                                            progress = data.get("data", {}).get("progress")
                                            if progress:
                                                print(f"⏳ {progress}%: {message}")
                                            else:
                                                print(f"⏳ {message}")
                                                
                                        elif response_type == "result":
                                            print("✅ 스케줄 생성 완료!")
                                            result_data = data.get("data", {})
                                            content = result_data.get("content", {})
                                            file_path = result_data.get("file_path", "")
                                            
                                            print(f"📄 스케줄 내용: {json.dumps(content, ensure_ascii=False, indent=2)[:500]}...")
                                            if file_path:
                                                print(f"💾 저장된 파일: {file_path}")
                                            
                                            return True
                                            
                                        elif response_type == "ai_response":
                                            ai_message = data.get("data", {}).get("message", "")
                                            print(f"🤖 AI 응답: {ai_message}")
                                            
                                            if "완료" in ai_message or "생성" in ai_message:
                                                return True
                                                
                                        elif response_type == "error":
                                            error_message = data.get("data", {}).get("message", "")
                                            print(f"❌ 오류: {error_message}")
                                            return False
                                            
                                    except asyncio.TimeoutError:
                                        print("⏰ 10초 응답 대기 타임아웃")
                                        continue
                                    except Exception as recv_error:
                                        print(f"❌ 응답 수신 오류: {str(recv_error)}")
                                        break
                                
                                print("⏰ 최대 대기 시간 초과")
                                return False
                            else:
                                print(f"❌ 예상치 못한 입력 요청: {input_required}")
                                return False
                        else:
                            print(f"❌ 마감일 입력 요청 대신 다른 응답: {data.get('type')}")
                            return False
                    else:
                        print(f"❌ 중요도 입력 요청 대신 다른 입력 요청: {input_required}")
                        return False
                else:
                    print(f"❌ 중요도 입력 요청 대신 다른 응답: {data.get('type')}")
                    return False
            else:
                print(f"❌ 파일 선택 요청 대신 다른 응답: {data.get('type')}")
                return False
                
    except Exception as e:
        print(f"❌ 테스트 실패: {str(e)}")
        return False

async def run_schedule_debug():
    """스케줄 디버그 테스트 실행"""
    print("🧪 Schedule 기능 상세 디버깅")
    print("=" * 50)
    
    try:
        success = await test_schedule_step_by_step()
        
        if success:
            print("\n🎉 Schedule 테스트 성공!")
        else:
            print("\n❌ Schedule 테스트 실패")
            
    except KeyboardInterrupt:
        print("\n⛔ 사용자에 의해 테스트 중단")
    except Exception as e:
        print(f"\n💥 예상치 못한 오류: {str(e)}")

if __name__ == "__main__":
    asyncio.run(run_schedule_debug())