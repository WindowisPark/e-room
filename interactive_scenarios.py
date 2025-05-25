# interactive_scenarios.py - 체계적인 대화형 테스트 시나리오

import asyncio
import websockets
import json
from datetime import datetime

class WebSocketScenarioTester:
    def __init__(self, host="localhost", port=8000):
        self.host = host
        self.port = port
        self.websocket = None
        self.session_id = None
        
    async def connect(self, user_id="scenario_test_user"):
        """WebSocket 연결"""
        uri = f"ws://{self.host}:{self.port}/api/v1/ws/chat/{user_id}"
        try:
            self.websocket = await websockets.connect(uri)
            print(f"✅ 연결 성공: {uri}")
            return True
        except Exception as e:
            print(f"❌ 연결 실패: {e}")
            return False
    
    async def send_message(self, message_type, data):
        """메시지 전송"""
        if not self.websocket:
            return False
        
        message = {
            "type": message_type,
            "session_id": self.session_id,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        await self.websocket.send(json.dumps(message, ensure_ascii=False))
        print(f"📤 전송: {message_type} - {json.dumps(data, ensure_ascii=False)}")
        return True
    
    async def wait_for_response(self, timeout=10):
        """응답 대기"""
        try:
            response = await asyncio.wait_for(self.websocket.recv(), timeout=timeout)
            data = json.loads(response)
            self.session_id = data.get("session_id", self.session_id)
            return data
        except asyncio.TimeoutError:
            print(f"⏰ 응답 대기 시간 초과 ({timeout}초)")
            return None
        except Exception as e:
            print(f"❌ 응답 수신 오류: {e}")
            return None
    
    async def handle_response(self, response):
        """응답 처리 및 자동 대응"""
        if not response:
            return False
        
        msg_type = response.get("type")
        print(f"📥 수신: {msg_type}")
        
        if msg_type == "ai_response":
            message = response['data']['message']
            task_type = response['data'].get('task_type', 'unknown')
            print(f"🤖 AI ({task_type}): {message[:200]}...")
            return True
            
        elif msg_type == "file_request":
            req_data = response['data']
            print(f"📂 파일 요청: {req_data['message']}")
            print(f"   타입: {req_data['request_type']}")
            print(f"   다중: {req_data['multiple']}, 선택사항: {req_data['optional']}")
            
            # 자동 응답
            if req_data['optional']:
                print("⏭️  선택사항 스킵")
                await self.send_message("file_selection", {
                    "selected_files": [],
                    "skip": True
                })
            else:
                fake_file = f"test_{req_data['request_type']}.pdf"
                print(f"📄 가상 파일 선택: {fake_file}")
                await self.send_message("file_selection", {
                    "selected_files": [fake_file],
                    "skip": False
                })
            return True
            
        elif msg_type == "status_update":
            status = response['data']['status']
            message = response['data']['message']
            progress = response['data'].get('progress', '')
            if progress:
                print(f"⏳ {status}: {message} ({progress}%)")
            else:
                print(f"⏳ {status}: {message}")
            return True
            
        elif msg_type == "result":
            task_type = response['data']['task_type']
            print(f"🎯 결과 ({task_type}) 수신 완료!")
            return True
            
        elif msg_type == "error":
            error_msg = response['data']['message']
            print(f"❌ 오류: {error_msg}")
            return False
            
        return True
    
    async def run_conversation(self, steps, timeout_per_step=15):
        """대화 시나리오 실행"""
        for i, step in enumerate(steps, 1):
            print(f"\n📋 단계 {i}/{len(steps)}: {step['description']}")
            
            if step['type'] == 'user_message':
                await self.send_message("user_message", {"message": step['content']})
            elif step['type'] == 'importance_input':
                await self.send_message("importance_input", step['content'])
            elif step['type'] == 'deadline_input':
                await self.send_message("deadline_input", step['content'])
            elif step['type'] == 'wait':
                await asyncio.sleep(step['duration'])
                continue
            
            # 응답들을 계속 처리 (여러 개 올 수 있음)
            response_count = 0
            max_responses = step.get('max_responses', 5)
            
            while response_count < max_responses:
                response = await self.wait_for_response(timeout_per_step)
                if not response:
                    break
                
                if not await self.handle_response(response):
                    print(f"❌ 단계 {i} 실패")
                    return False
                
                response_count += 1
                
                # 특정 조건에서 다음 단계로
                if response.get('type') in ['result', 'ai_response']:
                    if response.get('type') == 'result' or 'is_final' in response.get('data', {}):
                        break
                
                # 잠시 대기
                await asyncio.sleep(0.5)
        
        return True
    
    async def disconnect(self):
        """연결 해제"""
        if self.websocket:
            await self.websocket.close()

# 테스트 시나리오 정의
QA_SCENARIO = [
    {
        "description": "QA 질문 1 - 기본 개념",
        "type": "user_message",
        "content": "안녕하세요! 정보보호에서 대칭키 암호화가 뭔가요?",
        "max_responses": 3
    },
    {
        "description": "QA 질문 2 - 추가 질문",
        "type": "user_message", 
        "content": "그럼 비대칭키 암호화와의 차이점은 뭔가요?",
        "max_responses": 2
    },
    {
        "description": "QA 질문 3 - 실습 관련",
        "type": "user_message",
        "content": "AES 알고리즘을 실제로 구현할 때 주의사항은?",
        "max_responses": 2
    }
]

SUMMARY_SCENARIO = [
    {
        "description": "요약 요청",
        "type": "user_message",
        "content": "업로드된 운영체제 자료를 요약해주세요",
        "max_responses": 10  # 파일 선택 + 상태 업데이트 + 결과
    },
    {
        "description": "요약 결과에 대한 질문",
        "type": "user_message",
        "content": "요약된 내용 중에서 가장 중요한 부분은 뭔가요?",
        "max_responses": 2
    }
]

EXAM_SCENARIO = [
    {
        "description": "시험 문제 생성 요청",
        "type": "user_message", 
        "content": "정보보호 시험문제를 만들어주세요",
        "max_responses": 15  # 기출문제 선택 + 학습자료 선택 + 생성 과정
    },
    {
        "description": "생성된 문제에 대한 질문",
        "type": "user_message",
        "content": "첫 번째 문제의 정답과 해설을 알려주세요",
        "max_responses": 2
    }
]

SCHEDULER_SCENARIO = [
    {
        "description": "스케줄 생성 요청",
        "type": "user_message",
        "content": "다음 주 중간고사 대비 학습 일정을 짜주세요",
        "max_responses": 5  # 파일 선택 요청
    },
    {
        "description": "잠시 대기",
        "type": "wait",
        "duration": 2
    },
    {
        "description": "중요도 입력 (텍스트)",
        "type": "user_message",
        "content": "정보보호: 5, 네트워크: 4, 운영체제: 3",
        "max_responses": 3
    },
    {
        "description": "마감일 입력 (텍스트)",
        "type": "user_message", 
        "content": "정보보호: 2025-06-01, 네트워크: 2025-06-03, 운영체제: 2025-06-05",
        "max_responses": 8  # 스케줄 생성 과정
    },
    {
        "description": "생성된 일정에 대한 질문",
        "type": "user_message",
        "content": "이 일정에서 하루에 몇 시간씩 공부해야 하나요?",
        "max_responses": 2
    }
]

async def run_scenario_test(scenario_name, scenario_steps):
    """시나리오 테스트 실행"""
    print(f"\n🎬 {scenario_name} 시나리오 테스트 시작")
    print("=" * 60)
    
    tester = WebSocketScenarioTester()
    
    if not await tester.connect(f"{scenario_name.lower()}_user"):
        return False
    
    try:
        success = await tester.run_conversation(scenario_steps)
        if success:
            print(f"\n✅ {scenario_name} 시나리오 성공!")
        else:
            print(f"\n❌ {scenario_name} 시나리오 실패!")
        return success
        
    except Exception as e:
        print(f"\n💥 {scenario_name} 시나리오 예외 발생: {e}")
        return False
    finally:
        await tester.disconnect()

async def run_all_scenarios():
    """모든 시나리오 테스트 실행"""
    scenarios = [
        ("QA", QA_SCENARIO),
        ("Summary", SUMMARY_SCENARIO), 
        ("Exam", EXAM_SCENARIO),
        ("Scheduler", SCHEDULER_SCENARIO)
    ]
    
    results = {}
    
    for name, steps in scenarios:
        print(f"\n{'='*20} {name} 테스트 {'='*20}")
        results[name] = await run_scenario_test(name, steps)
        
        # 시나리오 간 간격
        await asyncio.sleep(2)
    
    # 결과 요약
    print(f"\n{'='*20} 테스트 결과 요약 {'='*20}")
    for name, success in results.items():
        status = "✅ 성공" if success else "❌ 실패"
        print(f"{name:12}: {status}")
    
    success_count = sum(results.values())
    total_count = len(results)
    print(f"\n전체 결과: {success_count}/{total_count} 성공")
    
    return success_count == total_count

if __name__ == "__main__":
    print("🎭 WebSocket 대화형 시나리오 테스트")
    print("각 기능별로 실제 대화 플로우를 테스트합니다.")
    
    try:
        result = asyncio.run(run_all_scenarios())
        if result:
            print("\n🎉 모든 시나리오 테스트 성공!")
        else:
            print("\n💥 일부 시나리오 테스트 실패!")
    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n💥 테스트 실행 중 오류: {e}")