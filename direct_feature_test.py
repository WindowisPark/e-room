# direct_feature_test.py - 목적 판단 우회하여 직접 테스트

import asyncio
import websockets
import json
from datetime import datetime

async def test_summary_direct():
    """요약 기능 직접 테스트"""
    print("📄 Summary 직접 테스트...")
    
    # 더 명확한 요약 요청
    messages = [
        "PDF 파일을 요약해주세요",
        "문서 요약을 해주세요", 
        "자료를 정리해서 요약해주세요"
    ]
    
    for i, msg in enumerate(messages, 1):
        print(f"\n🧪 요약 테스트 {i}: {msg}")
        
        try:
            async with websockets.connect("ws://localhost:8000/api/v1/ws/chat/summary_direct_user") as ws:
                message = {
                    "type": "user_message",
                    "session_id": None,
                    "data": {"message": msg},
                    "timestamp": datetime.now().isoformat()
                }
                
                await ws.send(json.dumps(message, ensure_ascii=False))
                
                # 응답 대기
                for _ in range(5):
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=15)
                        data = json.loads(response)
                        msg_type = data.get("type")
                        
                        print(f"📥 {msg_type}")
                        
                        if msg_type == "file_request":
                            req_type = data["data"]["request_type"]
                            print(f"✅ 요약 분기 성공! 파일 요청: {req_type}")
                            return True
                        elif msg_type == "error":
                            print(f"❌ 오류: {data['data']['message']}")
                            break
                        elif msg_type == "ai_response":
                            task_type = data["data"].get("task_type", "unknown")
                            if task_type == "summary":
                                print("✅ 요약 모드로 분기됨!")
                                return True
                            else:
                                print(f"⚠️ QA 모드로 분기됨 ({task_type})")
                                break
                                
                    except asyncio.TimeoutError:
                        print("⏰ 시간 초과")
                        break
                        
        except Exception as e:
            print(f"❌ 연결 오류: {e}")
    
    return False

async def test_scheduler_direct():
    """스케줄러 기능 직접 테스트"""
    print("\n📅 Scheduler 직접 테스트...")
    
    # 더 명확한 스케줄 요청
    messages = [
        "학습 계획을 세워주세요",
        "시험 일정을 짜주세요",
        "공부 스케줄을 만들어주세요"
    ]
    
    for i, msg in enumerate(messages, 1):
        print(f"\n🧪 스케줄 테스트 {i}: {msg}")
        
        try:
            async with websockets.connect("ws://localhost:8000/api/v1/ws/chat/scheduler_direct_user") as ws:
                message = {
                    "type": "user_message",
                    "session_id": None,
                    "data": {"message": msg},
                    "timestamp": datetime.now().isoformat()
                }
                
                await ws.send(json.dumps(message, ensure_ascii=False))
                
                # 응답 대기
                for _ in range(5):
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=15)
                        data = json.loads(response)
                        msg_type = data.get("type")
                        
                        print(f"📥 {msg_type}")
                        
                        if msg_type == "file_request":
                            req_type = data["data"]["request_type"]
                            if req_type == "scheduler_materials":
                                print(f"✅ 스케줄러 분기 성공! 파일 요청: {req_type}")
                                return True
                            else:
                                print(f"⚠️ 다른 기능으로 분기됨: {req_type}")
                        elif msg_type == "error":
                            print(f"❌ 오류: {data['data']['message']}")
                            break
                        elif msg_type == "ai_response":
                            task_type = data["data"].get("task_type", "unknown")
                            if task_type == "schedule":
                                print("✅ 스케줄러 모드로 분기됨!")
                                return True
                            else:
                                print(f"⚠️ 다른 모드로 분기됨 ({task_type})")
                                break
                                
                    except asyncio.TimeoutError:
                        print("⏰ 시간 초과")
                        break
                        
        except Exception as e:
            print(f"❌ 연결 오류: {e}")
    
    return False

async def test_purpose_detection():
    """목적 판단 로직 테스트"""
    print("\n🎯 목적 판단 테스트...")
    
    test_cases = [
        ("QA 질문", "AES 암호화가 뭐야?", "qa"),
        ("요약 요청", "이 자료를 요약해줘", "summary"),
        ("시험 요청", "시험문제 만들어줘", "generate_exam"),
        ("일정 요청", "학습 일정 짜줘", "schedule")
    ]
    
    results = {}
    
    for name, message, expected in test_cases:
        print(f"\n🧪 {name}: '{message}'")
        
        try:
            async with websockets.connect(f"ws://localhost:8000/api/v1/ws/chat/purpose_test_{expected}") as ws:
                msg = {
                    "type": "user_message",
                    "session_id": None,
                    "data": {"message": message},
                    "timestamp": datetime.now().isoformat()
                }
                
                await ws.send(json.dumps(msg, ensure_ascii=False))
                
                # 첫 번째 응답으로 목적 판단 결과 확인
                detected_purpose = None
                
                for _ in range(3):
                    try:
                        response = await asyncio.wait_for(ws.recv(), timeout=10)
                        data = json.loads(response)
                        msg_type = data.get("type")
                        
                        if msg_type == "file_request":
                            req_type = data["data"]["request_type"]
                            if req_type == "summary_target":
                                detected_purpose = "summary"
                            elif req_type == "previous_exam":
                                detected_purpose = "generate_exam"
                            elif req_type == "scheduler_materials":
                                detected_purpose = "schedule"
                            break
                        elif msg_type == "ai_response":
                            task_type = data["data"].get("task_type", "qa")
                            detected_purpose = task_type
                            break
                        elif msg_type == "error":
                            print(f"❌ 오류: {data['data']['message']}")
                            detected_purpose = "error"
                            break
                            
                    except asyncio.TimeoutError:
                        detected_purpose = "timeout"
                        break
                
                results[name] = {
                    "expected": expected,
                    "detected": detected_purpose,
                    "success": detected_purpose == expected
                }
                
                if detected_purpose == expected:
                    print(f"✅ 성공: {expected}")
                else:
                    print(f"❌ 실패: 예상 {expected}, 실제 {detected_purpose}")
                    
        except Exception as e:
            print(f"❌ 테스트 오류: {e}")
            results[name] = {"expected": expected, "detected": "error", "success": False}
    
    return results

async def main():
    print("🔧 목적 판단 및 기능별 직접 테스트")
    print("=" * 60)
    
    # 1. 목적 판단 테스트
    purpose_results = await test_purpose_detection()
    
    # 2. Summary 직접 테스트
    summary_success = await test_summary_direct()
    
    # 3. Scheduler 직접 테스트  
    scheduler_success = await test_scheduler_direct()
    
    # 결과 요약
    print(f"\n{'='*20} 종합 결과 {'='*20}")
    
    print("🎯 목적 판단 결과:")
    success_count = 0
    for name, result in purpose_results.items():
        status = "✅" if result["success"] else "❌"
        print(f"  {status} {name}: {result['expected']} → {result['detected']}")
        if result["success"]:
            success_count += 1
    
    print(f"\n📊 기능별 테스트:")
    print(f"  Summary:   {'✅' if summary_success else '❌'}")
    print(f"  Scheduler: {'✅' if scheduler_success else '❌'}")
    
    total_purpose_tests = len(purpose_results)
    print(f"\n🎯 목적 판단: {success_count}/{total_purpose_tests} 성공")
    
    if success_count < total_purpose_tests:
        print("\n💡 해결 방안:")
        print("1. LLM 프롬프트 개선 (목적 판단 정확도 향상)")
        print("2. 키워드 기반 사전 필터링 추가")
        print("3. 사용자 의도 명확화 UI 추가")

if __name__ == "__main__":
    asyncio.run(main())