# app/services/email_service.py

import asyncio
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

class EmailService:
    """
    이메일 발송 서비스
    
    SMTP를 통한 이메일 발송 기능을 제공합니다.
    개발 환경에서는 실제 발송 대신 로그로 시뮬레이션합니다.
    """
    
    def __init__(self):
        self.smtp_server = getattr(settings, 'SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = getattr(settings, 'SMTP_PORT', 587)
        self.smtp_username = getattr(settings, 'SMTP_USERNAME', '')
        self.smtp_password = getattr(settings, 'SMTP_PASSWORD', '')
        self.from_email = getattr(settings, 'FROM_EMAIL', 'noreply@planova.kr')
        self.environment = getattr(settings, 'ENVIRONMENT', 'development')

    async def send_password_reset_email(
        self, 
        to_email: str, 
        reset_token: str, 
        user_name: str
    ) -> bool:
        """
        비밀번호 재설정 이메일 발송
        
        Args:
            to_email: 수신자 이메일
            reset_token: 재설정 토큰
            user_name: 사용자 이름
            
        Returns:
            발송 성공 여부
        """
        try:
            # 재설정 링크 생성
            frontend_url = getattr(settings, 'FRONTEND_URL', 'https://planova.kr')
            reset_url = f"{frontend_url}/auth/reset-password?token={reset_token}"
            
            # 이메일 제목 및 내용
            subject = "[Planova] 비밀번호 재설정 요청"
            html_content = self._get_reset_email_template(user_name, reset_url)
            
            # 이메일 발송
            return await self._send_email(to_email, subject, html_content)
            
        except Exception as e:
            logger.error(f"비밀번호 재설정 이메일 발송 실패: {str(e)}")
            return False

    def _get_reset_email_template(self, user_name: str, reset_url: str) -> str:
        """
        비밀번호 재설정 이메일 HTML 템플릿 생성
        
        Args:
            user_name: 사용자 이름
            reset_url: 재설정 링크
            
        Returns:
            HTML 이메일 내용
        """
        return f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>비밀번호 재설정</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    background-color: #f8f9fa;
                    margin: 0;
                    padding: 0;
                }}
                .container {{
                    max-width: 600px;
                    margin: 40px auto;
                    background-color: #ffffff;
                    border-radius: 12px;
                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                    overflow: hidden;
                }}
                .header {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px 40px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                    font-weight: 600;
                }}
                .content {{
                    padding: 40px;
                }}
                .greeting {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #2c3e50;
                    margin-bottom: 20px;
                }}
                .message {{
                    font-size: 16px;
                    color: #555;
                    margin-bottom: 30px;
                    line-height: 1.6;
                }}
                .button-container {{
                    text-align: center;
                    margin: 40px 0;
                }}
                .reset-button {{
                    display: inline-block;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 16px 32px;
                    text-decoration: none;
                    border-radius: 8px;
                    font-weight: 600;
                    font-size: 16px;
                    transition: transform 0.2s ease;
                }}
                .reset-button:hover {{
                    transform: translateY(-2px);
                }}
                .warning {{
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 8px;
                    padding: 16px;
                    margin: 20px 0;
                    color: #856404;
                }}
                .warning-title {{
                    font-weight: 600;
                    margin-bottom: 8px;
                }}
                .footer {{
                    background-color: #f8f9fa;
                    padding: 20px 40px;
                    text-align: center;
                    border-top: 1px solid #e9ecef;
                }}
                .footer p {{
                    margin: 0;
                    color: #6c757d;
                    font-size: 14px;
                }}
                .divider {{
                    height: 1px;
                    background-color: #e9ecef;
                    margin: 30px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🔐 비밀번호 재설정</h1>
                </div>
                
                <div class="content">
                    <div class="greeting">안녕하세요, {user_name}님!</div>
                    
                    <div class="message">
                        Planova 계정의 비밀번호 재설정을 요청하셨습니다.<br>
                        아래 버튼을 클릭하여 새로운 비밀번호를 설정해 주세요.
                    </div>
                    
                    <div class="button-container">
                        <a href="{reset_url}" class="reset-button">
                            비밀번호 재설정하기
                        </a>
                    </div>
                    
                    <div class="warning">
                        <div class="warning-title">⚠️ 중요한 보안 안내</div>
                        <ul style="margin: 8px 0; padding-left: 20px;">
                            <li>이 링크는 <strong>30분간</strong>만 유효합니다.</li>
                            <li>링크는 일회용으로, 사용 후 자동으로 만료됩니다.</li>
                            <li>비밀번호 재설정을 요청하지 않으셨다면, 이 이메일을 무시하세요.</li>
                        </ul>
                    </div>
                    
                    <div class="divider"></div>
                    
                    <div style="color: #6c757d; font-size: 14px;">
                        위 버튼이 작동하지 않는다면, 다음 링크를 복사하여 브라우저에서 직접 접속하세요:<br>
                        <a href="{reset_url}" style="color: #667eea; word-break: break-all;">{reset_url}</a>
                    </div>
                </div>
                
                <div class="footer">
                    <p>
                        © 2024 Planova. All rights reserved.<br>
                        이 이메일은 자동으로 발송되었습니다. 답장하지 마세요.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

    async def _send_email(self, to_email: str, subject: str, html_content: str) -> bool:
        """
        실제 이메일 발송 처리

        Args:
            to_email: 수신자 이메일
            subject: 제목
            html_content: HTML 내용

        Returns:
            발송 성공 여부
        """
        # 개발 모드에서는 콘솔에 로그만 출력
        if self.environment == "development" or not self.smtp_username:
            logger.info("=" * 60)
            logger.info("📧 [개발모드] 이메일 발송 시뮬레이션")
            logger.info("=" * 60)
            logger.info(f"📤 To: {to_email}")
            logger.info(f"📋 Subject: {subject}")
            logger.info(f"🔗 Reset Link: {self._extract_reset_link(html_content)}")
            logger.info("=" * 60)
            return True

        # 운영 모드에서는 실제 SMTP 발송 (블로킹 I/O를 스레드로 이동)
        try:
            # 이메일 메시지 구성
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email

            # HTML 파트 추가
            html_part = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(html_part)

            # SMTP 블로킹 호출을 스레드풀에서 실행
            await asyncio.to_thread(self._smtp_send_sync, msg)
            logger.info(f"✅ 이메일 발송 성공: {to_email}")
            return True

        except smtplib.SMTPAuthenticationError:
            logger.error("❌ SMTP 인증 실패: 이메일 계정 정보를 확인하세요")
            return False
        except smtplib.SMTPRecipientsRefused:
            logger.error(f"❌ 수신자 거부됨: {to_email}")
            return False
        except smtplib.SMTPServerDisconnected:
            logger.error("❌ SMTP 서버 연결 끊어짐")
            return False
        except Exception as e:
            logger.error(f"❌ 이메일 발송 실패: {str(e)}")
            return False

    def _smtp_send_sync(self, msg: MIMEMultipart) -> None:
        """
        동기 SMTP 호출 (asyncio.to_thread로 감싸져서 실행됨)

        Args:
            msg: MIME 메시지 객체
        """
        with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
            server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)

    def _extract_reset_link(self, html_content: str) -> str:
        """개발 모드 로깅을 위한 재설정 링크 추출"""
        try:
            import re
            match = re.search(r'href="([^"]*reset-password[^"]*)"', html_content)
            return match.group(1) if match else "링크 추출 실패"
        except:
            return "링크 추출 실패"

    async def send_welcome_email(self, to_email: str, user_name: str) -> bool:
        """
        회원가입 환영 이메일 발송 (향후 확장용)
        """
        # 향후 구현 예정
        pass

    async def send_notification_email(
        self, 
        to_email: str, 
        subject: str, 
        message: str
    ) -> bool:
        """
        일반 알림 이메일 발송 (향후 확장용)
        """
        # 향후 구현 예정
        pass