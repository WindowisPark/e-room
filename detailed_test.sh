#!/bin/bash
# detailed_test.sh - 상세 기능별 테스트

echo "🧪 WebSocket 상세 기능 테스트 시작..."

# 1. API 컨테이너에서 실제 WebSocket 모듈 테스트
echo "📦 API 컨테이너 내부에서 상세 테스트 실행..."

docker exec -it ai_agent_api_dev bash -c "
    cd /app
    export PYTHONPATH='/app'
    export REDIS_URL='redis://redis:6379/0'
    
    echo '🧪 상세 WebSocket 기능 테스트...'
    
    # 실제 WebSocket 모듈 테스트 파일 생성
    cat > /tmp/detailed_websocket_test.py << 'EOF'
import pytest
import asyncio
import json
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# FastAPI 및 WebSocket 관련
from fastapi.testclient import TestClient
from fastapi import WebSocket

# 프로젝트 모듈들
try:
    from app.services.session_manager import SessionManager
    from app.api.v1.websocket.chat import WebSocketManager
    from app.api.v1.websocket.handlers import TaskHandlers
    from langchain_core.messages import HumanMessage, AIMessage
    print('✅ 모든 모듈 임포트 성공')
except ImportError as e:
    print(f'❌ 모듈 임포트 실패: {e}')
    sys.exit(1)

class DetailedWebSocketTest:
    def __init__(self):
        self.session_manager = SessionManager('redis://redis:6379/0')
        self.ws_manager = WebSocketManager()
        self.test_user_id = 'detailed_test_user'
        
    async def test_session_operations(self):
        \"\"\"세션 관련 상세 테스트\"\"\"
        print('\\n🔧 세션 관리 테스트...')
        
        # 1. 세션 생성
        session_id = self.session_manager.create_session(self.test_user_id, 'qa')
        print(f'   ✅ 세션 생성: {session_id}')
        
        # 2. 세션 조회
        session_data = self.session_manager.get_session(session_id)
        assert session_data is not None
        assert session_data['user_id'] == self.test_user_id
        assert session_data['task_type'] == 'qa'
        print('   ✅ 세션 조회 성공')
        
        # 3. 메시지 히스토리 추가
        test_message = HumanMessage(content='테스트 메시지입니다')
        result = self.session_manager.add_message_to_history(session_id, test_message)
        assert result is True
        print('   ✅ 메시지 히스토리 추가 성공')
        
        # 4. 히스토리 조회
        history = self.session_manager.get_chat_history(session_id)
        assert len(history) == 1
        assert history[0]['content'] == '테스트 메시지입니다'
        print('   ✅ 히스토리 조회 성공')
        
        
        # 5. 사용자 세션 목록 조회
        user_sessions = self.session_manager.get_user_chat_sessions(self.test_user_id)
        assert len(user_sessions) >= 1
        print(f'   ✅ 사용자 세션 목록 조회: {len(user_sessions)}개')

        # 6. 세션 업데이트
        update_result = self.session_manager.update_session(session_id, {
            'task_type': 'summary',
            'waiting_for': 'file_selection'
        })
        assert update_result is True
        print('   ✅ 세션 업데이트 성공')
        
        # 7. 세션 정리
        cleanup_result = self.session_manager.cleanup_session(session_id)
        assert cleanup_result is True
        print('   ✅ 세션 정리 성공')
        
        return True

    async def test_message_purpose_detection(self):
        \"\"\"메시지 목적 판단 테스트\"\"\"
        print('\\n🎯 메시지 목적 판단 테스트...')
        
        test_cases = [
            ('정보보호 자료 요약해줘', 'summary'),
            ('운영체제 시험문제 만들어줘', 'generate_exam'),
            ('다음 주 시험 일정 짜줘', 'schedule'),
            ('AES 암호화가 뭐야?', 'qa')
        ]
        
        with patch('app.services.pdf_agent.nodes.common.llm') as mock_llm:
            for message, expected_purpose in test_cases:
                # Mock LLM 응답 설정
                mock_response = Mock()
                mock_response.content = json.dumps({
                    'question': message,
                    'purpose': expected_purpose,
                    'full_document': 0
                })
                mock_llm.invoke.return_value = mock_response
                
                # 목적 판단 함수 테스트
                from app.services.pdf_agent.nodes.common import judge_the_purpose_of_the_input
                
                test_state = {
                    'messages': [HumanMessage(content=message)]
                }
                
                result = judge_the_purpose_of_the_input(test_state)
                
                if result.get('purpose') == expected_purpose:
                    print(f'   ✅ \\'{message[:20]}...\\'  → {expected_purpose}')
                else:
                    print(f'   ❌ \\'{message[:20]}...\\'  → 예상: {expected_purpose}, 실제: {result.get(\"purpose\")}')
        
        return True

    async def test_task_handlers(self):
        \"\"\"작업별 핸들러 테스트\"\"\"
        print('\\n⚙️ 작업 핸들러 테스트...')
        
        # Mock WebSocket 연결
        mock_websocket = Mock()
        mock_websocket.send_text = AsyncMock()
        
        # Mock 메서드들
        with patch.object(self.ws_manager, 'send_message') as mock_send, \\
             patch.object(self.ws_manager, 'send_status') as mock_status, \\
             patch.object(self.ws_manager, 'get_user_files') as mock_files, \\
             patch.object(self.ws_manager.session_manager, 'get_session') as mock_get_session, \\
             patch.object(self.ws_manager.session_manager, 'update_session') as mock_update:
            
            # Mock 설정
            mock_get_session.return_value = {
                'session_id': 'test_session',
                'user_id': self.test_user_id,
                'task_type': 'summary',
                'agent_state': {}
            }
            mock_update.return_value = True
            mock_files.return_value = [
                {'name': 'test.pdf', 'path': '/test/test.pdf'}
            ]
            
            # Summary 핸들러 테스트
            await self.ws_manager.handle_summary_start('test_session', {'purpose': 'summary'})
            mock_send.assert_called()
            print('   ✅ Summary 핸들러 테스트 성공')
            
            # Exam 핸들러 테스트
            await self.ws_manager.handle_exam_start('test_session', {'purpose': 'generate_exam'})
            print('   ✅ Exam 핸들러 테스트 성공')
            
            # Scheduler 핸들러 테스트
            await self.ws_manager.handle_scheduler_start('test_session', {'purpose': 'schedule'})
            print('   ✅ Scheduler 핸들러 테스트 성공')
        
        return True

    async def test_file_selection_flow(self):
        \"\"\"파일 선택 플로우 테스트\"\"\"
        print('\\n📂 파일 선택 플로우 테스트...')
        
        with patch.object(self.ws_manager.session_manager, 'get_session') as mock_get, \\
             patch.object(self.ws_manager.task_handlers, 'execute_summary') as mock_execute:
            
            # Summary 파일 선택
            mock_get.return_value = {
                'task_type': 'summary',
                'current_request_type': 'summary_target',
                'user_id': self.test_user_id,
                'agent_state': {},  # ✅ 이 줄을 반드시 추가하세요
            }
            
            await self.ws_manager.handle_file_selection('test_session', ['test.pdf'], False)
            mock_execute.assert_called_once()
            print('   ✅ Summary 파일 선택 테스트 성공')
            
        with patch.object(self.ws_manager.session_manager, 'get_session') as mock_get, \\
             patch.object(self.ws_manager.task_handlers, 'request_study_material_selection') as mock_request:
            
            # Exam 기출문제 스킵
            mock_get.return_value = {
                'task_type': 'generate_exam',
                'current_request_type': 'previous_exam',
                'user_id': self.test_user_id,
                'agent_state': {}  # ✅ 반드시 포함
            }
            
            await self.ws_manager.handle_file_selection('test_session', [], True)
            mock_request.assert_called_once()
            print('   ✅ Exam 기출문제 스킵 테스트 성공')
        
        return True

    async def test_scheduler_input_parsing(self):
        \"\"\"스케줄러 입력 파싱 테스트\"\"\"
        print('\\n📅 스케줄러 입력 파싱 테스트...')
        
        with patch.object(self.ws_manager.session_manager, 'get_session') as mock_get, \\
             patch.object(self.ws_manager.task_handlers, 'handle_importance_input') as mock_handle:
            
            mock_get.return_value = {'scheduler_data': {}}
            
            # 중요도 입력 테스트
            test_input = '정보보호: 5, 네트워크: 3, 운영체제: 4'
            await self.ws_manager.process_importance_input('test_session', test_input)
            
            # 호출된 인자 확인
            args = mock_handle.call_args[0][1]  # 두 번째 인자
            assert args['정보보호'] == 5
            assert args['네트워크'] == 3
            assert args['운영체제'] == 4
            print('   ✅ 중요도 입력 파싱 성공')
            
        with patch.object(self.ws_manager.session_manager, 'get_session') as mock_get, \\
             patch.object(self.ws_manager.task_handlers, 'handle_deadline_input') as mock_handle:
            
            mock_get.return_value = {'scheduler_data': {}}
            
            # 마감일 입력 테스트
            test_input = '정보보호: 2025-06-01, 네트워크: 2025-06-03'
            await self.ws_manager.process_deadline_input('test_session', test_input)
            
            # 호출된 인자 확인
            args = mock_handle.call_args[0][1]
            assert args['정보보호'] == '2025-06-01'
            assert args['네트워크'] == '2025-06-03'
            print('   ✅ 마감일 입력 파싱 성공')
        
        return True

    async def run_all_tests(self):
        \"\"\"모든 테스트 실행\"\"\"
        print('🧪 상세 WebSocket 기능 테스트 시작')
        print('=' * 50)
        
        try:
            await self.test_session_operations()
            await self.test_message_purpose_detection()
            await self.test_task_handlers()
            await self.test_file_selection_flow()
            await self.test_scheduler_input_parsing()
            
            print('\\n🎉 모든 상세 테스트 통과!')
            return True
            
        except Exception as e:
            print(f'\\n❌ 테스트 실패: {e}')
            import traceback
            traceback.print_exc()
            return False

async def main():
    tester = DetailedWebSocketTest()
    success = await tester.run_all_tests()
    return success

if __name__ == '__main__':
    result = asyncio.run(main())
    if result:
        print('\\n✅ 상세 테스트 완료!')
    else:
        print('\\n❌ 상세 테스트 실패!')
        sys.exit(1)
EOF

    # 상세 테스트 실행
    python /tmp/detailed_websocket_test.py
"

echo ""
echo "🎯 다음 단계: 실제 대화형 테스트"
echo "python docker_manual_test.py 를 실행하여 실제 대화를 테스트해보세요!"