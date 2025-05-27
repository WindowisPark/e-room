# real_environment_test.py
"""
실제 S3 환경에서 PDF Agent 전체 기능 테스트 (JWT 인증 포함)
"""

import asyncio
import websockets
import json
import aiohttp
import aiofiles
import os
from pathlib import Path

class RealEnvironmentTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.ws_url = "ws://localhost:8000/api/v1/ws/improved-chat"
        self.user_id = "2"  # 실제 user_id
        self.folder_name = "정보보호"
        self.auth_token = None  # JWT 토큰 저장
        
    async def login(self):
        """JWT 토큰 발급받기"""
        print("🔐 사용자 로그인 중...")
        login_url = f"{self.base_url}/api/v1/auth/login"
        login_payload = {
            "email": "jose5744@naver.com",
            "password": "shawnchang7"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(login_url, json=login_payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.auth_token = data.get("access_token")
                        if self.auth_token:
                            print("✅ 로그인 성공, JWT 토큰 획득")
                            return True
                        else:
                            print("❌ 토큰이 응답에 없음")
                            return False
                    else:
                        error_text = await response.text()
                        print(f"❌ 로그인 실패 ({response.status}): {error_text}")
                        return False
        except Exception as e:
            print(f"❌ 로그인 중 오류: {str(e)}")
            return False
    
    def get_auth_headers(self):
        """인증 헤더 반환"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}
        
    async def step1_check_server(self):
        """1단계: 서버 상태 확인"""
        print("📡 1단계: 서버 상태 확인")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/api/health") as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✅ 서버 정상: {data['status']}")
                        return True
                    else:
                        print(f"❌ 서버 응답 이상: {response.status}")
                        return False
        except Exception as e:
            print(f"❌ 서버 연결 실패: {str(e)}")
            return False
    
    async def step2_upload_pdf(self, pdf_path):
        """2단계: 실제 PDF 파일 업로드 (JWT 인증 포함)"""
        print(f"📤 2단계: PDF 파일 업로드 - {pdf_path}")
        
        if not os.path.exists(pdf_path):
            print(f"❌ 파일을 찾을 수 없음: {pdf_path}")
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                with open(pdf_path, 'rb') as f:
                    data = aiohttp.FormData()
                    data.add_field('files', f, 
                                 filename=os.path.basename(pdf_path),
                                 content_type='application/pdf')
                    
                    upload_url = f"{self.base_url}/api/v1/pdf/users/{self.user_id}/folders/{self.folder_name}/files"
                    headers = self.get_auth_headers()
                    
                    print(f"📡 업로드 URL: {upload_url}")
                    print(f"🔐 인증 헤더: {'Bearer ***' if self.auth_token else '없음'}")
                    
                    async with session.post(upload_url, data=data, headers=headers) as response:
                        if response.status == 200:
                            result = await response.json()
                            print(f"✅ 업로드 성공: {result}")
                            return True
                        else:
                            error_text = await response.text()
                            print(f"❌ 업로드 실패 ({response.status}): {error_text}")
                            return False
                            
        except Exception as e:
            print(f"❌ 업로드 중 오류: {str(e)}")
            return False
    
    async def step3_check_files(self):
        """3단계: 업로드된 파일 확인 (JWT 인증 포함)"""
        print("📁 3단계: 업로드된 파일 확인")
        
        try:
            async with aiohttp.ClientSession() as session:
                headers = self.get_auth_headers()
                
                # 폴더 목록 확인
                folders_url = f"{self.base_url}/api/v1/pdf/users/{self.user_id}/folders"
                async with session.get(folders_url, headers=headers) as response:
                    if response.status == 200:
                        folders = await response.json()
                        print(f"📁 사용자 폴더: {[f['name'] for f in folders]}")
                        
                        # 정보보호 폴더 내 파일 확인
                        files_url = f"{self.base_url}/api/v1/pdf/users/{self.user_id}/folders/{self.folder_name}/files"
                        async with session.get(files_url, headers=headers) as response:
                            if response.status == 200:
                                files = await response.json()
                                print(f"📄 {self.folder_name} 폴더 파일: {files}")
                                return files
                            else:
                                error_text = await response.text()
                                print(f"❌ 파일 목록 조회 실패 ({response.status}): {error_text}")
                                return []
                    else:
                        error_text = await response.text()
                        print(f"❌ 폴더 목록 조회 실패 ({response.status}): {error_text}")
                        return []
                        
        except Exception as e:
            print(f"❌ 파일 확인 중 오류: {str(e)}")
            return []
    
    async def step4_test_websocket_qa(self):
        """4단계: QA 기능 테스트"""
        print("💬 4단계: QA 기능 테스트")
        
        try:
            ws_url = f"{self.ws_url}/{self.user_id}"
            async with websockets.connect(ws_url) as websocket:
                print("✅ WebSocket 연결 성공")
                
                # QA 질문
                qa_message = {
                    "type": "user_message",
                    "data": {"message": "정보보호의 기본 원칙은 무엇인가요?"}
                }
                
                await websocket.send(json.dumps(qa_message, ensure_ascii=False))
                print("📤 QA 질문 전송")
                
                response = await asyncio.wait_for(websocket.recv(), timeout=15)
                data = json.loads(response)
                
                if data.get("type") == "ai_response":
                    answer = data.get("data", {}).get("message", "")
                    print(f"✅ QA 응답 수신: {answer[:100]}...")
                    return True
                else:
                    print(f"❌ 예상치 못한 응답: {data.get('type')}")
                    return False
                    
        except Exception as e:
            print(f"❌ QA 테스트 실패: {str(e)}")
            return False
    
    async def step5_test_summary(self, files):
        """5단계: 요약 기능 테스트 (실제 파일 사용)"""
        print("📄 5단계: 요약 기능 테스트")
        
        if not files:
            print("❌ 요약할 파일이 없음")
            return False
        
        try:
            ws_url = f"{self.ws_url}/{self.user_id}"
            async with websockets.connect(ws_url) as websocket:
                print("✅ WebSocket 연결 성공")
                
                # 요약 요청
                summary_message = {
                    "type": "user_message",
                    "data": {"message": "문서를 요약해주세요"}
                }
                
                await websocket.send(json.dumps(summary_message, ensure_ascii=False))
                print("📤 요약 요청 전송")
                
                # 파일 선택 요청 대기
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)
                
                if data.get("type") == "file_request":
                    print("✅ 파일 선택 요청 수신")
                    available_files = data.get("data", {}).get("available_files", [])
                    print(f"📁 사용 가능한 파일: {len(available_files)}개")
                    
                    if available_files:
                        # 첫 번째 파일 선택
                        selected_file = available_files[0]
                        file_selection = {
                            "type": "file_selection",
                            "data": {
                                "selected_files": [selected_file["path"]],
                                "skip": False
                            }
                        }
                        
                        await websocket.send(json.dumps(file_selection))
                        print(f"📤 파일 선택: {selected_file['name']}")
                        
                        # 요약 진행 과정 모니터링
                        return await self._monitor_task_progress(websocket, "summary")
                    else:
                        print("❌ 사용 가능한 파일이 없음")
                        return False
                else:
                    print(f"❌ 파일 요청 대신 다른 응답: {data.get('type')}")
                    return False
                    
        except Exception as e:
            print(f"❌ 요약 테스트 실패: {str(e)}")
            return False
    
    async def step6_test_exam(self, files):
        """6단계: 시험 문제 생성 테스트"""
        print("📝 6단계: 시험 문제 생성 테스트")
        
        if not files:
            print("❌ 시험 문제 생성할 파일이 없음")
            return False
        
        try:
            ws_url = f"{self.ws_url}/{self.user_id}"
            async with websockets.connect(ws_url) as websocket:
                print("✅ WebSocket 연결 성공")
                
                # 시험 문제 생성 요청
                exam_message = {
                    "type": "user_message",
                    "data": {"message": "시험 문제를 만들어주세요"}
                }
                
                await websocket.send(json.dumps(exam_message, ensure_ascii=False))
                print("📤 시험 문제 생성 요청 전송")
                
                # 기출문제 선택 요청 대기
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)
                
                if data.get("type") == "file_request":
                    print("✅ 기출문제 선택 요청 수신")
                    
                    # 기출문제 스킵
                    skip_selection = {
                        "type": "file_selection",
                        "data": {
                            "selected_files": [],
                            "skip": True
                        }
                    }
                    
                    await websocket.send(json.dumps(skip_selection))
                    print("📤 기출문제 선택 스킵")
                    
                    # 학습자료 선택 요청 대기
                    response = await asyncio.wait_for(websocket.recv(), timeout=10)
                    data = json.loads(response)
                    
                    if data.get("type") == "file_request":
                        print("✅ 학습자료 선택 요청 수신")
                        available_files = data.get("data", {}).get("available_files", [])
                        
                        if available_files:
                            # 첫 번째 파일 선택
                            selected_file = available_files[0]
                            file_selection = {
                                "type": "file_selection",
                                "data": {
                                    "selected_files": [selected_file["path"]],
                                    "skip": False
                                }
                            }
                            
                            await websocket.send(json.dumps(file_selection))
                            print(f"📤 학습자료 선택: {selected_file['name']}")
                            
                            # 시험 문제 생성 과정 모니터링
                            return await self._monitor_task_progress(websocket, "exam")
                        else:
                            print("❌ 사용 가능한 학습자료가 없음")
                            return False
                    else:
                        print(f"❌ 학습자료 요청 대신 다른 응답: {data.get('type')}")
                        return False
                else:
                    print(f"❌ 기출문제 요청 대신 다른 응답: {data.get('type')}")
                    return False
                    
        except Exception as e:
            print(f"❌ 시험 문제 생성 테스트 실패: {str(e)}")
            return False
    
    async def step7_test_schedule(self, files):
        """7단계: 학습 계획 수립 테스트"""
        print("📅 7단계: 학습 계획 수립 테스트")
        
        if not files:
            print("❌ 학습 계획 수립할 파일이 없음")
            return False
        
        try:
            ws_url = f"{self.ws_url}/{self.user_id}"
            async with websockets.connect(ws_url) as websocket:
                print("✅ WebSocket 연결 성공")
                
                # 학습 계획 수립 요청
                schedule_message = {
                    "type": "user_message",
                    "data": {"message": "정보보호 과목 학습 계획을 짜주세요"}
                }
                
                await websocket.send(json.dumps(schedule_message, ensure_ascii=False))
                print("📤 학습 계획 수립 요청 전송")
                
                # 파일 선택 요청 대기
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)
                
                if data.get("type") == "file_request":
                    print("✅ 학습자료 선택 요청 수신")
                    available_files = data.get("data", {}).get("available_files", [])
                    
                    if available_files:
                        # 첫 번째 파일 선택
                        selected_file = available_files[0]
                        file_selection = {
                            "type": "file_selection",
                            "data": {
                                "selected_files": [selected_file["path"]],
                                "skip": False
                            }
                        }
                        
                        await websocket.send(json.dumps(file_selection))
                        print(f"📤 학습자료 선택: {selected_file['name']}")
                        
                        # 중요도 입력 요청 대기
                        response = await asyncio.wait_for(websocket.recv(), timeout=10)
                        data = json.loads(response)
                        
                        if data.get("type") == "ai_response":
                            input_required = data.get("data", {}).get("input_required")
                            if input_required == "importance":
                                print("✅ 중요도 입력 요청 수신")
                                
                                # 중요도 입력
                                importance_message = {
                                    "type": "user_message",
                                    "data": {"message": "정보보호: 5"}
                                }
                                
                                await websocket.send(json.dumps(importance_message, ensure_ascii=False))
                                print("📤 중요도 입력: 정보보호: 5")
                                
                                # 마감일 입력 요청 대기
                                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                                data = json.loads(response)
                                
                                if data.get("type") == "ai_response":
                                    input_required = data.get("data", {}).get("input_required")
                                    if input_required in ["deadline", "deadlines"]:
                                        print("✅ 마감일 입력 요청 수신")
                                        
                                        # 마감일 입력
                                        deadline_message = {
                                            "type": "user_message",
                                            "data": {"message": "정보보호: 2025-06-15"}
                                        }
                                        
                                        await websocket.send(json.dumps(deadline_message, ensure_ascii=False))
                                        print("📤 마감일 입력: 정보보호: 2025-06-15")
                                        
                                        # 학습 계획 생성 과정 모니터링
                                        return await self._monitor_task_progress(websocket, "schedule")
                                    else:
                                        print(f"❌ 마감일 입력 대신 다른 요청: {input_required}")
                                        return False
                                else:
                                    print(f"❌ 마감일 요청 대신 다른 응답: {data.get('type')}")
                                    return False
                            else:
                                print(f"❌ 중요도 입력 대신 다른 요청: {input_required}")
                                return False
                        else:
                            print(f"❌ 중요도 요청 대신 다른 응답: {data.get('type')}")
                            return False
                    else:
                        print("❌ 사용 가능한 파일이 없음")
                        return False
                else:
                    print(f"❌ 파일 요청 대신 다른 응답: {data.get('type')}")
                    return False
                    
        except Exception as e:
            print(f"❌ 학습 계획 테스트 실패: {str(e)}")
            return False
    
    async def _monitor_task_progress(self, websocket, task_type):
        """작업 진행 과정 모니터링"""
        print(f"⏳ {task_type} 작업 진행 모니터링...")
        
        start_time = asyncio.get_event_loop().time()
        max_wait_time = 120  # 최대 2분 대기
        
        while asyncio.get_event_loop().time() - start_time < max_wait_time:
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=15)
                data = json.loads(response)
                response_type = data.get("type")
                
                if response_type == "status_update":
                    status_data = data.get("data", {})
                    message = status_data.get("message", "")
                    progress = status_data.get("progress")
                    
                    if progress:
                        print(f"⏳ 진행률 {progress}%: {message}")
                    else:
                        print(f"⏳ {message}")
                        
                elif response_type == "result":
                    print(f"✅ {task_type} 완료!")
                    result_data = data.get("data", {})
                    content = result_data.get("content", "")
                    file_path = result_data.get("file_path", "")
                    
                    if isinstance(content, str):
                        print(f"📄 결과 미리보기: {content[:200]}...")
                    else:
                        print(f"📄 결과 데이터: {str(content)[:200]}...")
                    
                    if file_path:
                        print(f"💾 저장된 파일: {file_path}")
                    
                    return True
                    
                elif response_type == "ai_response":
                    ai_data = data.get("data", {})
                    message = ai_data.get("message", "")
                    if "완료" in message or "생성" in message:
                        print(f"✅ {task_type} 완료: {message}")
                        return True
                    else:
                        print(f"🤖 AI 응답: {message}")
                        
                elif response_type == "error":
                    error_data = data.get("data", {})
                    error_message = error_data.get("message", "")
                    print(f"❌ 오류 발생: {error_message}")
                    return False
                    
            except asyncio.TimeoutError:
                print("⏰ 15초 응답 대기 타임아웃")
                continue
                
        print("⏰ 최대 대기 시간 초과")
        return False

async def run_complete_test():
    """전체 테스트 실행 (로그인 포함)"""
    tester = RealEnvironmentTester()
    
    print("🧪 실제 환경 PDF Agent 종합 테스트")
    print("=" * 60)
    print(f"👤 사용자 ID: {tester.user_id}")
    print(f"📁 폴더명: {tester.folder_name}")
    print("=" * 60)
    
    results = []
    
    try:
        # 0단계: 로그인
        if not await tester.login():
            print("❌ 로그인 실패. 테스트 중단.")
            return
        results.append(("로그인", True))
        
        # 1단계: 서버 확인
        if not await tester.step1_check_server():
            print("❌ 서버 확인 실패. 테스트 중단.")
            return
        results.append(("서버 확인", True))
        
        # PDF 파일 찾기 (현재 디렉토리에서)
        pdf_files = []
        current_dir = Path(".")
        
        # 특정 위치에서 PDF 찾기
        search_paths = [
            "*.pdf",
            "**/*.pdf",  # 하위 디렉토리 포함
        ]
        
        for pattern in search_paths:
            for pdf_file in current_dir.glob(pattern):
                if pdf_file.is_file() and pdf_file.suffix.lower() == '.pdf':
                    pdf_files.append(str(pdf_file))
                    if len(pdf_files) >= 3:  # 최대 3개만
                        break
            if len(pdf_files) >= 3:
                break
        
        # 없으면 테스트용 PDF 생성 제안
        if not pdf_files:
            print("❌ 현재 디렉토리에서 PDF 파일을 찾을 수 없습니다.")
            print("💡 테스트용 PDF 파일을 현재 디렉토리에 넣어주세요.")
            
            # 파일 없이 WebSocket 테스트만 진행
            print("\n🔄 파일 없이 WebSocket 기능만 테스트합니다...")
            
            # QA 테스트
            qa_result = await tester.step4_test_websocket_qa()
            results.append(("QA 테스트", qa_result))
            
        else:
            print(f"📄 발견된 PDF 파일: {pdf_files}")
            
            # 2단계: PDF 업로드
            upload_success = False
            for pdf_file in pdf_files:
                if await tester.step2_upload_pdf(pdf_file):
                    upload_success = True
                    break  # 하나만 성공하면 충분
            
            results.append(("PDF 업로드", upload_success))
            
            # 3단계: 파일 확인
            files = await tester.step3_check_files()
            results.append(("파일 확인", len(files) > 0))
            
            # 4-7단계: 모든 기능 테스트
            qa_result = await tester.step4_test_websocket_qa()
            results.append(("QA 테스트", qa_result))
            
            if files:
                summary_result = await tester.step5_test_summary(files)
                results.append(("요약 테스트", summary_result))
                
                exam_result = await tester.step6_test_exam(files)
                results.append(("시험 문제 생성", exam_result))
                
                schedule_result = await tester.step7_test_schedule(files)
                results.append(("학습 계획 수립", schedule_result))
            else:
                print("⚠️ 파일이 없어서 파일 기반 기능은 스킵합니다.")
        
        # 결과 요약
        print("\n📊 테스트 결과 요약")
        print("=" * 60)
        
        for test_name, success in results:
            status = "✅ 성공" if success else "❌ 실패"
            print(f"{test_name}: {status}")
        
        success_count = sum(1 for _, success in results if success)
        print(f"\n📈 전체 결과: {success_count}/{len(results)} 통과")
        
        if success_count == len(results):
            print("🎉 모든 테스트 통과! PDF Agent가 완벽하게 작동합니다!")
        elif success_count >= len(results) * 0.7:  # 70% 이상
            print("✅ 대부분의 테스트 통과! 시스템이 정상 작동합니다!")
        else:
            print("⚠️ 일부 테스트 실패. 로그를 확인해주세요.")
            
    except KeyboardInterrupt:
        print("\n⛔ 사용자에 의해 테스트 중단")
    except Exception as e:
        print(f"\n💥 예상치 못한 오류: {str(e)}")

if __name__ == "__main__":
    print("🚀 실제 환경 PDF Agent 테스트 도구 (JWT 인증)")
    print("=" * 60)
    
    asyncio.run(run_complete_test())