# docker_manual_test.py - 도커 환경용 수동 테스트 클라이언트

import asyncio
import websockets
import json
import sys
from datetime import datetime

class DockerWebSocketClient:
    def __init__(self, host="localhost", port=8000, user_id="docker_test_user"):
        self.host = host
        self.port = port
        self.user_id = user_id
        self.websocket = None
        self.session_id = None
        
    async def connect(self):
        """도커 WebSocket 서버에 연결"""
        uri = f"ws://{self.host}:{self.port}/api/v1/ws/chat/{self.user_id}"
        try:
            print(f"🐳 도커 WebSocket 서버 연결 중...")
            print(f"📡 URI: {uri}")
            
            self.websocket = await websockets.connect(uri)
            print(f"✅ 연결 성공!")
            return True
            
        except websockets.exceptions.InvalidURI as e:
            print(f"❌ 잘못된 URI: {e}")
            return False
        except websockets.exceptions.ConnectionRefused as e:
            print(f"❌ 연결 거부됨. 서버가 실행 중인지 확인하세요: {e}")
            print("💡 다음 명령으로 API 서버 상태 확인:")
            print("   docker logs ai_agent_api_dev")
            return False
        except Exception as e:
            print(f"❌ 연결 실패: {e}")
            return False
    
    async def send_message(self, message_type, data):
        """메시지 전송"""
        if not self.websocket:
            print("❌ WebSocket이 연결되지 않았습니다.")
            return False
        
        message = {
            "type": message_type,
            "session_id": self.session_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            await self.websocket.send(json.dumps(message, ensure_ascii=False))
            print(f"📤 전송: {message_type}")
            return True
        except Exception as e:
            print(f"❌ 메시지 전송 실패: {e}")
            return False
    
    async def receive_messages(self):
        """메시지 수신"""
        if not self.websocket:
            return
        
        try:
            async for message in self.websocket:
                data = json.loads(message)
                await self.handle_message(data)
        except websockets.exceptions.ConnectionClosed:
            print("🔌 WebSocket 연결이 종료되었습니다.")
        except Exception as e:
            print(f"❌ 메시지 수신 오류: {e}")
    
    async def handle_message(self, data):
        """수신 메시지 처리"""
        msg_type = data.get("type")
        self.session_id = data.get("session_id", self.session_id)
        
        print(f"\n📥 수신: {msg_type}")
        
        if msg_type == "ai_response":
            message = data['data']['message']
            task_type = data['data'].get('task_type', 'unknown')
            print(f"🤖 AI ({task_type}): {message[:100]}...")
            
        elif msg_type == "file_request":
            req_data = data['data']
            print(f"📂 파일 요청: {req_data['message']}")
            print(f"   타입: {req_data['request_type']}")
            print(f"   다중선택: {req_data['multiple']}")
            print(f"   선택사항: {req_data['optional']}")
            
            # 시뮬레이션: 자동으로 첫 번째 파일 선택 또는 스킵
            if req_data['optional']:
                print("⏭️  선택사항이므로 스킵합니다.")
                await self.send_message("file_selection", {
                    "selected_files": [],
                    "skip": True
                })
            else:
                # 가상 파일 선택
                fake_file = f"docker_test_{req_data['request_type']}.pdf"
                print(f"📄 가상 파일 선택: {fake_file}")
                await self.send_message("file_selection", {
                    "selected_files": [fake_file],
                    "skip": False
                })
            
        elif msg_type == "status_update":
            status_data = data['data']
            status = status_data['status']
            message = status_data['message']
            progress = status_data.get('progress', '')
            if progress:
                print(f"⏳ {status}: {message} ({progress}%)")
            else:
                print(f"⏳ {status}: {message}")
            
        elif msg_type == "result":
            result_data = data['data']
            task_type = result_data['task_type']
            content = result_data['content']
            print(f"🎯 결과 ({task_type}):")
            if isinstance(content, str):
                print(f"   📄 {content[:200]}...")
            else:
                print(f"   📊 {type(content).__name__} 데이터")
            
        elif msg_type == "error":
            error_msg = data['data']['message']
            print(f"❌ 오류: {error_msg}")
            
        else:
            print(f"❓ 알 수 없는 메시지: {msg_type}")
    
    async def disconnect(self):
        """연결 해제"""
        if self.websocket:
            await self.websocket.close()
            print("🔌 연결 해제됨")

async def test_docker_scenarios():
    """도커 환경 시나리오 테스트"""
    print("🐳 도커 환경 WebSocket 테스트")
    print("=" * 50)
    
    client = DockerWebSocketClient()
    
    if not await client.connect():
        print("\n💡 문제 해결 방법:")
        print("1. API 서버 상태 확인: docker logs ai_agent_api_dev")
        print("2. 포트 확인: docker ps (8000 포트 매핑 확인)")
        print("3. 서버 재시작: docker restart ai_agent_api_dev")
        return
    
    # 백그라운드 메시지 수신
    receive_task = asyncio.create_task(client.receive_messages())
    
    try:
        scenarios = [
            ("QA 테스트", "안녕하세요! 정보보호에서 AES 암호화가 뭔가요?"),
            ("요약 테스트", "업로드된 자료를 요약해주세요"),
            ("시험 문제 테스트", "정보보호 시험문제를 만들어주세요"),
            ("스케줄 테스트", "다음 주 시험 일정을 짜주세요")
        ]
        
        for scenario_name, message in scenarios:
            print(f"\n🧪 {scenario_name} 시작...")
            await client.send_message("user_message", {"message": message})
            
            # 응답 대기
            await asyncio.sleep(3)
            
            print(f"✅ {scenario_name} 완료")
            
        print("\n🎉 모든 시나리오 테스트 완료!")
        
    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n❌ 테스트 중 오류 발생: {e}")
    finally:
        receive_task.cancel()
        await client.disconnect()

async def interactive_docker_test():
    """대화형 도커 테스트"""
    print("🎮 도커 환경 대화형 테스트")
    print("명령어: q(질문), s(요약), e(시험), c(일정), exit(종료)")
    
    client = DockerWebSocketClient()
    
    if not await client.connect():
        return
    
    receive_task = asyncio.create_task(client.receive_messages())
    
    try:
        while True:
            command = input("\n📝 명령어: ").strip().lower()
            
            if command == "exit":
                break
            elif command == "q":
                message = input("질문: ")
                await client.send_message("user_message", {"message": message})
            elif command == "s":
                await client.send_message("user_message", {"message": "자료 요약해주세요"})
            elif command == "e":
                await client.send_message("user_message", {"message": "시험문제 만들어주세요"})
            elif command == "c":
                await client.send_message("user_message", {"message": "학습 일정 짜주세요"})
            else:
                print("❓ 알 수 없는 명령어")
            
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 테스트 종료")
    finally:
        receive_task.cancel()
        await client.disconnect()

def check_docker_environment():
    """도커 환경 사전 점검"""
    import subprocess
    import sys
    
    print("🔍 도커 환경 사전 점검...")
    
    try:
        # Docker 명령어 확인
        result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Docker가 실행되지 않았습니다.")
            return False
        
        # API 컨테이너 확인
        if 'ai_agent_api_dev' not in result.stdout:
            print("❌ ai_agent_api_dev 컨테이너를 찾을 수 없습니다.")
            return False
        
        # Redis 컨테이너 확인
        if 'ai_agent_redis' not in result.stdout:
            print("❌ ai_agent_redis 컨테이너를 찾을 수 없습니다.")
            return False
        
        print("✅ 도커 환경 점검 완료")
        return True
        
    except FileNotFoundError:
        print("❌ Docker가 설치되지 않았습니다.")
        return False
    except Exception as e:
        print(f"❌ 환경 점검 실패: {e}")
        return False

if __name__ == "__main__":
    if not check_docker_environment():
        sys.exit(1)
    
    print("\n테스트 모드 선택:")
    print("1: 자동 시나리오 테스트")
    print("2: 대화형 테스트")
    
    choice = input("선택 (1-2): ").strip()
    
    if choice == "1":
        asyncio.run(test_docker_scenarios())
    elif choice == "2":
        asyncio.run(interactive_docker_test())
    else:
        print("❌ 잘못된 선택입니다.")