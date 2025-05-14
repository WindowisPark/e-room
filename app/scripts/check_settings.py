from app.core.config import settings
import os

print("환경 변수 설정 확인:")
print(f"REDIS_HOST: {os.getenv('REDIS_HOST', '(설정되지 않음)')}")
print(f"REDIS_PORT: {os.getenv('REDIS_PORT', '(설정되지 않음)')}")
print(f"REDIS_URL: {os.getenv('REDIS_URL', '(설정되지 않음)')}")

print("\nSettings 객체에서의 설정:")
print(f"settings.REDIS_HOST: {settings.REDIS_HOST}")
print(f"settings.REDIS_PORT: {settings.REDIS_PORT}")
print(f"settings.REDIS_URL: {settings.REDIS_URL}")
