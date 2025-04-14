# scripts/migration_gamification.py
import sys
import os
from pathlib import Path

# 프로젝트 루트를 path에 추가
root_path = Path(__file__).parent.parent
sys.path.append(str(root_path))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

def main():
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URI)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    inspector = inspect(engine)
    
    try:
        print("게이미피케이션 필드 추가 중...")
        
        # User 테이블에 필드 추가
        columns = [c['name'] for c in inspector.get_columns('users')]
        
        if 'points' not in columns:
            db.execute(text('ALTER TABLE users ADD COLUMN points INTEGER DEFAULT 0'))
            print("- points 필드 추가됨")
        
        if 'level' not in columns:
            db.execute(text('ALTER TABLE users ADD COLUMN level INTEGER DEFAULT 1'))
            print("- level 필드 추가됨")
        
        if 'streak_days' not in columns:
            db.execute(text('ALTER TABLE users ADD COLUMN streak_days INTEGER DEFAULT 0'))
            print("- streak_days 필드 추가됨")
            
        print("게이미피케이션 테이블 생성 중...")
        
        # 테이블 존재 여부 확인 및 생성
        tables = inspector.get_table_names()
        
        if 'point_history' not in tables:
            db.execute(text('''
            CREATE TABLE point_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                action_type VARCHAR(50) NOT NULL,
                points INTEGER NOT NULL,
                description VARCHAR(255) NOT NULL,
                reference_id INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
            '''))
            print("- point_history 테이블 생성됨")
        
        if 'badges' not in tables:
            db.execute(text('''
            CREATE TABLE badges (
                id SERIAL PRIMARY KEY,
                code VARCHAR(50) UNIQUE NOT NULL,
                name VARCHAR(50) NOT NULL,
                description VARCHAR(255) NOT NULL,
                image_url VARCHAR(255) NOT NULL,
                badge_type VARCHAR(50) NOT NULL,
                required_level INTEGER,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
            '''))
            print("- badges 테이블 생성됨")
        
        if 'user_badges' not in tables:
            db.execute(text('''
            CREATE TABLE user_badges (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                badge_id INTEGER NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
                acquired_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
            '''))
            print("- user_badges 테이블 생성됨")
            
        db.commit()
        print("게이미피케이션 데이터베이스 스키마 업데이트 완료!")
        
    except Exception as e:
        db.rollback()
        print(f"오류 발생: {str(e)}")
    finally:
        db.close()

if __name__ == "__main__":
    main()