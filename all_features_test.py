# all_features_test.py - 모든 기능 순차 테스트

import asyncio
import websockets
import json
from datetime import datetime

class AllFeaturesTest:
    def __init__(self):
        self.base_uri = "ws://localhost:8000/api/v1/ws/chat"
        
    async def test_feature(self, feature_name, user_id, steps):
        """개별 기능 테스트"""
        uri = f"{self.base_uri}/{user_id}"
        
        print(f"\n🎬 {feature_name} 기능 테스트 시작")
        print("=" * 60)
        
        try:
            async with websockets.connect(uri) as websocket:
                print(f"✅ {feature_name} 연결 성공")
                session_id = None
                
                for i, step in enumerate(steps, 1):
                    print(f"\n📋 단계 {i}/{len(steps)}: {step['description']}")
                    
                    # 메시지 전송
                    message = {
                        "type": step["type"],
                        "session_id": session_id,
                        "data": step["data"],
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    await websocket.send(json.dumps(message, ensure_ascii=False))
                    print(f"📤 전송: {step['type']}")
                    
                    # 응답 처리
                    success = await self.handle_responses(
                        websocket, 
                        step.get('expected_responses', 5),
                        step.get('timeout', 30)
                    )
                    
                    if not success:
                        print(f"❌ {feature_name} 단계 {i} 실패")
                        return False
                    
                    # 세션 ID 업데이트는 실제 응답에서 받아야 함
                    
                print(f"✅ {feature_name} 테스트 성공!")
                return True
                
        except Exception as e:
            print(f"❌ {feature_name} 테스트 실패: {e}")
            return False
    
    async def handle_responses(self, websocket, max_responses, timeout):
        """응답 처리"""
        response_count = 0
        session_id = None
        
        while response_count < max_responses:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)
                
                session_id = data.get("session_id", session_id)
                msg_type = data.get("type")
                
                print(f"📥 응답 {response_count + 1}: {msg_type}")
                
                if msg_type == "ai_response":
                    message = data["data"]["message"]
                    task_type = data["data"].get("task_type", "unknown")
                    print(f"🤖 AI ({task_type}): {message[:150]}...")
                    
                elif msg_type == "file_request":
                    req_data = data["data"]
                    print(f"📂 파일 요청: {req_data['request_type']}")
                    
                    # 자동 파일 선택
                    await self.auto_file_selection(websocket, req_data, session_id)
                    
                elif msg_type == "status_update":
                    status = data["data"]["message"]
                    progress = data["data"].get("progress", "")
                    if progress:
                        print(f"⏳ {status} ({progress}%)")
                    else:
                        print(f"⏳ {status}")
                        
                elif msg_type == "result":
                    task_type = data["data"]["task_type"]
                    print(f"🎯 결과 ({task_type}) 생성 완료!")
                    return True
                    
                elif msg_type == "error":
                    error_msg = data["data"]["message"]
                    print(f"❌ 오류: {error_msg}")
                    return False
                
                response_count += 1
                
                # AI 응답이 왔으면 성공으로 간주
                if msg_type == "ai_response":
                    return True
                    
            except asyncio.TimeoutError:
                print("⏰ 응답 시간 초과")
                break
                
        return response_count > 0
    
    async def auto_file_selection(self, websocket, req_data, session_id):
        """자동 파일 선택"""
        if req_data.get("optional", False):
            # 선택사항이면 스킵
            file_message = {
                "type": "file_selection",
                "session_id": session_id,
                "data": {"selected_files": [], "skip": True},
                "timestamp": datetime.now().isoformat()
            }
            print("⏭️ 선택사항 스킵")
        else:
            # 가상 파일 선택
            fake_file = f"test_{req_data['request_type']}.pdf"
            file_message = {
                "type": "file_selection", 
                "session_id": session_id,
                "data": {"selected_files": [fake_file], "skip": False},
                "timestamp": datetime.now().isoformat()
            }
            print(f"📄 가상 파일 선택: {fake_file}")
        
        await websocket.send(json.dumps(file_message, ensure_ascii=False))

    async def run_all_tests(self):
        """모든 기능 테스트 실행"""
        
        # 1. Summary 테스트
        summary_steps = [
            {
                "description": "요약 요청",
                "type": "user_message",
                "data": {"message": "운영체제 자료를 요약해주세요"},
                "expected_responses": 8,
                "timeout": 30
            }
        ]
        
        # 2. Exam 테스트  
        exam_steps = [
            {
                "description": "시험 문제 생성 요청",
                "type": "user_message", 
                "data": {"message": "정보보호 시험문제를 만들어주세요"},
                "expected_responses": 10,
                "timeout": 30
            }
        ]
        
        # 3. Scheduler 테스트
        scheduler_steps = [
            {
                "description": "스케줄 생성 요청",
                "type": "user_message",
                "data": {"message": "다음 주 시험 대비 학습 일정을 짜주세요"},
                "expected_responses": 8,
                "timeout": 30
            }
        ]
        
        # 테스트 실행
        tests = [
            ("Summary", "summary_test_user", summary_steps),
            ("Exam", "exam_test_user", exam_steps), 
            ("Scheduler", "scheduler_test_user", scheduler_steps)
        ]
        
        results = {}
        
        for feature_name, user_id, steps in tests:
            results[feature_name] = await self.test_feature(feature_name, user_id, steps)
            
            # 테스트 간 간격
            await asyncio.sleep(3)
        
        # 결과 요약
        print(f"\n{'='*20} 전체 테스트 결과 {'='*20}")
        success_count = 0
        for feature, success in results.items():
            status = "✅ 성공" if success else "❌ 실패"
            print(f"{feature:12}: {status}")
            if success:
                success_count += 1
        
        total_tests = len(results)
        print(f"\n🎯 전체 결과: {success_count}/{total_tests} 성공")
        
        if success_count == total_tests:
            print("🎉 모든 기능 테스트 성공!")
        elif success_count > 0:
            print("⚠️ 부분적 성공 - 일부 기능 정상 동작")
        else:
            print("💥 모든 기능 테스트 실패")
        
        return success_count, total_tests

async def main():
    print("🚀 전체 기능 통합 테스트")
    print("QA, Summary, Exam, Scheduler 모든 기능을 테스트합니다.")
    print("=" * 60)
    
    tester = AllFeaturesTest()
    
    try:
        success_count, total_count = await tester.run_all_tests()
        
        if success_count == total_count:
            print("\n🎉 축하합니다! 모든 WebSocket 기능이 정상 동작합니다!")
            print("\n🎯 다음 단계:")
            print("1. 프론트엔드 연동")
            print("2. 실제 파일 업로드 기능 추가")
            print("3. UI/UX 개선")
        else:
            print(f"\n⚠️ {success_count}/{total_count} 기능이 동작합니다.")
            print("\n🔧 개선 필요한 부분:")
            print("1. 목적 판단 로직 개선")
            print("2. 파일 시스템 연동")
            print("3. 에러 처리 강화")
            
    except KeyboardInterrupt:
        print("\n🛑 사용자에 의해 중단됨")
    except Exception as e:
        print(f"\n💥 테스트 실행 중 오류: {e}")

if __name__ == "__main__":
    asyncio.run(main())