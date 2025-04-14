# app/scripts/init_badges.py
import sys
import os
from pathlib import Path

# 프로젝트 루트를 path에 추가
root_path = Path(__file__).parent.parent.parent
sys.path.append(str(root_path))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

def main():
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URI)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 기존 배지 수 확인
        result = db.execute(text("SELECT COUNT(*) FROM badges"))
        existing_count = result.scalar()
        print(f"기존 배지 수: {existing_count}")
        
        # 이미 배지가 있으면 스킵
        if existing_count > 0:
            print("이미 배지가 존재합니다. 초기화 작업을 건너뜁니다.")
            return
            
        # 배지 타입 정의
        badge_types = ["attendance", "annotation", "pdf", "team", "special", "event", "level"]
        
        # 초기 배지 데이터
        badges = [
            # 출석 관련 배지
            {
                "code": "attendance_first",
                "name": "첫 출석",
                "description": "처음으로 출석 체크를 완료했습니다.",
                "image_url": "/assets/badges/attendance_first.png",
                "badge_type": "attendance",
                "required_level": None
            },
            {
                "code": "attendance_week",
                "name": "일주일 연속 출석",
                "description": "7일 연속으로 출석 체크를 완료했습니다.",
                "image_url": "/assets/badges/attendance_week.png",
                "badge_type": "attendance",
                "required_level": None
            },
            {
                "code": "attendance_month",
                "name": "한 달 연속 출석",
                "description": "30일 연속으로 출석 체크를 완료했습니다.",
                "image_url": "/assets/badges/attendance_month.png",
                "badge_type": "attendance",
                "required_level": None
            },
            
            # 주석 관련 배지
            {
                "code": "annotation_first",
                "name": "첫 주석",
                "description": "처음으로 PDF에 주석을 작성했습니다.",
                "image_url": "/assets/badges/annotation_first.png",
                "badge_type": "annotation",
                "required_level": None
            },
            {
                "code": "annotation_master",
                "name": "주석 마스터",
                "description": "100개 이상의 주석을 작성했습니다.",
                "image_url": "/assets/badges/annotation_master.png",
                "badge_type": "annotation",
                "required_level": None
            },
            
            # PDF 관련 배지
            {
                "code": "pdf_first",
                "name": "첫 PDF",
                "description": "처음으로 PDF를 업로드했습니다.",
                "image_url": "/assets/badges/pdf_first.png",
                "badge_type": "pdf",
                "required_level": None
            },
            {
                "code": "pdf_collector",
                "name": "PDF 컬렉터",
                "description": "50개 이상의 PDF를 업로드했습니다.",
                "image_url": "/assets/badges/pdf_collector.png",
                "badge_type": "pdf",
                "required_level": None
            },
            
            # 팀 관련 배지
            {
                "code": "team_creator",
                "name": "팀 창설자",
                "description": "처음으로 팀을 생성했습니다.",
                "image_url": "/assets/badges/team_creator.png",
                "badge_type": "team",
                "required_level": None
            },
            {
                "code": "team_collaborator",
                "name": "협업 마스터",
                "description": "5개 이상의 팀에 참여했습니다.",
                "image_url": "/assets/badges/team_collaborator.png",
                "badge_type": "team",
                "required_level": None
            },
            
            # 레벨 관련 배지
            {
                "code": "level_5",
                "name": "성장하는 학자",
                "description": "레벨 5에 도달했습니다.",
                "image_url": "/assets/badges/level_5.png",
                "badge_type": "level",
                "required_level": 5
            },
            {
                "code": "level_10",
                "name": "지식의 대가",
                "description": "레벨 10에 도달했습니다.",
                "image_url": "/assets/badges/level_10.png",
                "badge_type": "level",
                "required_level": 10
            }
        ]
        
        # 배지 데이터 삽입
        for badge in badges:
            required_level = badge["required_level"] if badge["required_level"] else "NULL"
            sql = f"""
            INSERT INTO badges (code, name, description, image_url, badge_type, required_level)
            VALUES ('{badge["code"]}', '{badge["name"]}', '{badge["description"]}', 
            '{badge["image_url"]}', '{badge["badge_type"]}', {required_level})
            """
            db.execute(text(sql))
        
        db.commit()
        print(f"{len(badges)}개의 배지가 성공적으로 생성되었습니다.")
    
    except Exception as e:
        db.rollback()
        print(f"배지 생성 중 오류 발생: {str(e)}")
    
    finally:
        db.close()

if __name__ == "__main__":
    main()