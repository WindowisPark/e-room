# debug_tools.py
"""
디버깅용 도구들
"""

import logging
import json
from datetime import datetime

class WebSocketDebugger:
    """WebSocket 디버깅 도구"""
    
    @staticmethod
    def setup_detailed_logging():
        """상세 로깅 설정"""
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('websocket_debug.log'),
                logging.StreamHandler()
            ]
        )
        
        # 각 모듈별 로거 설정
        loggers = [
            'app.api.v1.websocket.improved_chat',
            'app.services.pdf_agent.adapters.websocket_adapter',
            'app.services.session_manager',
            'websockets'
        ]
        
        for logger_name in loggers:
            logger = logging.getLogger(logger_name)
            logger.setLevel(logging.DEBUG)
    
    @staticmethod
    def log_message_flow(message_type, data, direction="send"):
        """메시지 흐름 로깅"""
        timestamp = datetime.now().isoformat()
        arrow = "→" if direction == "send" else "←"
        
        print(f"\n{timestamp} {arrow} {message_type}")
        print(f"Data: {json.dumps(data, indent=2, ensure_ascii=False)}")
        print("-" * 50)
    
    @staticmethod
    def check_session_state(session_manager, session_id):
        """세션 상태 확인"""
        session_data = session_manager.get_session(session_id)
        if session_data:
            print(f"\n📊 세션 상태 ({session_id}):")
            print(f"Task Type: {session_data.get('task_type')}")
            print(f"Waiting For: {session_data.get('waiting_for')}")
            print(f"Current Request: {session_data.get('current_request_type')}")
            print(f"Agent State Keys: {list(session_data.get('agent_state', {}).keys())}")
        else:
            print(f"❌ 세션을 찾을 수 없음: {session_id}")