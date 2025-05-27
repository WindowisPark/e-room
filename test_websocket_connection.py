# test_websocket_connection.py
"""
개선된 WebSocket 연결 및 메시지 흐름 테스트
"""

import asyncio
import json
import websockets
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketTester:
    def __init__(self, user_id="123"):
        self.user_id = user_id
        self.ws_url = f"ws://localhost:8000/api/v1/ws/improved-chat/{user_id}"
        self.websocket = None
        
    async def connect(self):
        """WebSocket 연결"""
        try:
            self.websocket = await websockets.connect(self.ws_url)
            logger.info(f"✅ WebSocket 연결 성공: {self.ws_url}")
            return True
        except Exception as e:
            logger.error(f"❌ WebSocket 연결 실패: {str(e)}")
            return False
    
    async def send_message(self, message_type, data):
        """메시지 전송"""
        if not self.websocket:
            logger.error("WebSocket이 연결되지 않았습니다.")
            return
            
        message = {
            "type": message_type,
            "data": data
        }
        
        try:
            await self.websocket.send(json.dumps(message, ensure_ascii=False))
            logger.info(f"📤 전송: {message_type}")
            logger.debug(f"내용: {data}")
        except Exception as e:
            logger.error(f"❌ 메시지 전송 실패: {str(e)}")
    
    async def receive_message(self):
        """메시지 수신"""
        if not self.websocket:
            return None
            
        try:
            response = await self.websocket.recv()
            data = json.loads(response)
            logger.info(f"📥 수신: {data.get('type', 'unknown')}")
            logger.debug(f"내용: {data}")
            return data
        except Exception as e:
            logger.error(f"❌ 메시지 수신 실패: {str(e)}")
            return None
    
    async def test_basic_qa(self):
        """기본 QA 테스트"""
        logger.info("\n🧪 === QA 테스트 시작 ===")
        
        # 간단한 질문 전송
        await self.send_message("user_message", {
            "message": "안녕하세요. 파이썬이 뭔가요?"
        })
        
        # 응답 대기
        response = await self.receive_message()
        if response and response.get("type") == "ai_response":
            logger.info("✅ QA 테스트 성공")
            return True
        else:
            logger.error("❌ QA 테스트 실패")
            return False
    
    async def test_summary_flow(self):
        """요약 플로우 테스트"""
        logger.info("\n🧪 === Summary 테스트 시작 ===")
        
        # 요약 요청
        await self.send_message("user_message", {
            "message": "요약해줘"
        })
        
        # 파일 선택 요청 대기
        response = await self.receive_message()
        if response and response.get("type") == "file_request":
            logger.info("✅ 파일 선택 요청 수신")
            
            # 가상의 파일 선택
            await self.send_message("file_selection", {
                "selected_files": ["users/123/study/test.pdf"],
                "skip": False
            })
            
            # 결과 대기
            while True:
                result = await self.receive_message()
                if not result:
                    break
                    
                if result.get("type") == "result":
                    logger.info("✅ Summary 테스트 성공")
                    return True
                elif result.get("type") == "error":
                    logger.error(f"❌ Summary 오류: {result.get('data', {}).get('message')}")
                    return False
                elif result.get("type") == "status_update":
                    logger.info(f"⏳ 진행 중: {result.get('data', {}).get('message')}")
        
        logger.error("❌ Summary 테스트 실패")
        return False
    
    async def test_exam_flow(self):
        """시험 문제 생성 플로우 테스트"""
        logger.info("\n🧪 === Exam 테스트 시작 ===")
        
        # 시험 문제 생성 요청
        await self.send_message("user_message", {
            "message": "시험 문제 만들어줘"
        })
        
        # 기출문제 선택 요청 대기
        response = await self.receive_message()
        if response and response.get("type") == "file_request":
            logger.info("✅ 기출문제 선택 요청 수신")
            
            # 기출문제 스킵
            await self.send_message("file_selection", {
                "selected_files": [],
                "skip": True
            })
            
            # 학습자료 선택 요청 대기
            response2 = await self.receive_message()
            if response2 and response2.get("type") == "file_request":
                logger.info("✅ 학습자료 선택 요청 수신")
                
                # 학습자료 선택
                await self.send_message("file_selection", {
                    "selected_files": ["users/123/study/material.pdf"],
                    "skip": False
                })
                
                # 결과 대기
                while True:
                    result = await self.receive_message()
                    if not result:
                        break
                        
                    if result.get("type") == "result":
                        logger.info("✅ Exam 테스트 성공")
                        return True
                    elif result.get("type") == "error":
                        logger.error(f"❌ Exam 오류: {result.get('data', {}).get('message')}")
                        return False
        
        logger.error("❌ Exam 테스트 실패")
        return False
    
    async def test_schedule_flow(self):
        """스케줄러 플로우 테스트"""
        logger.info("\n🧪 === Schedule 테스트 시작 ===")
        
        # 스케줄 생성 요청
        await self.send_message("user_message", {
            "message": "학습 계획 짜줘"
        })
        
        # 학습자료 선택 요청 대기
        response = await self.receive_message()
        if response and response.get("type") == "file_request":
            logger.info("✅ 학습자료 선택 요청 수신")
            
            # 여러 파일 선택
            await self.send_message("file_selection", {
                "selected_files": [
                    "users/123/study/math.pdf",
                    "users/123/study/science.pdf"
                ],
                "skip": False
            })
            
            # 중요도 입력 요청 대기
            response2 = await self.receive_message()
            if response2 and response2.get("type") == "ai_response":
                data = response2.get("data", {})
                if data.get("input_required") == "importance":
                    logger.info("✅ 중요도 입력 요청 수신")
                    
                    # 중요도 입력 (텍스트 메시지로)
                    await self.send_message("user_message", {
                        "message": "math: 5, science: 4"
                    })
                    
                    # 마감일 입력 요청 대기
                    response3 = await self.receive_message()
                    if response3 and response3.get("type") == "ai_response":
                        data3 = response3.get("data", {})
                        if data3.get("input_required") == "deadline":
                            logger.info("✅ 마감일 입력 요청 수신")
                            
                            # 마감일 입력
                            await self.send_message("user_message", {
                                "message": "math: 2025-06-01, science: 2025-06-03"
                            })
                            
                            # 결과 대기
                            while True:
                                result = await self.receive_message()
                                if not result:
                                    break
                                    
                                if result.get("type") == "result":
                                    logger.info("✅ Schedule 테스트 성공")
                                    return True
                                elif result.get("type") == "error":
                                    logger.error(f"❌ Schedule 오류: {result.get('data', {}).get('message')}")
                                    return False
        
        logger.error("❌ Schedule 테스트 실패")
        return False
    
    async def close(self):
        """연결 종료"""
        if self.websocket:
            await self.websocket.close()
            logger.info("🔌 WebSocket 연결 종료")

async def run_all_tests():
    """모든 테스트 실행"""
    tester = WebSocketTester()
    
    # 연결 테스트
    if not await tester.connect():
        return
    
    try:
        # 각 기능별 테스트
        results = []
        
        results.append(("QA", await tester.test_basic_qa()))
        results.append(("Summary", await tester.test_summary_flow()))
        results.append(("Exam", await tester.test_exam_flow()))
        results.append(("Schedule", await tester.test_schedule_flow()))
        
        # 결과 요약
        logger.info("\n📊 === 테스트 결과 요약 ===")
        for test_name, success in results:
            status = "✅ 성공" if success else "❌ 실패"
            logger.info(f"{test_name}: {status}")
        
        success_count = sum(1 for _, success in results if success)
        logger.info(f"\n총 {success_count}/{len(results)} 테스트 통과")
        
    finally:
        await tester.close()

if __name__ == "__main__":
    # 개별 테스트 실행 예시
    async def test_connection_only():
        tester = WebSocketTester()
        if await tester.connect():
            logger.info("✅ 기본 연결 성공!")
            await tester.close()
        else:
            logger.error("❌ 기본 연결 실패!")
    
    # 연결만 테스트하려면
    # asyncio.run(test_connection_only())
    
    # 전체 테스트 실행
    asyncio.run(run_all_tests())
