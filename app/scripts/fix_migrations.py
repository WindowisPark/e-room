import os
import sys
import logging
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('fix_migrations')

# 프로젝트 루트 추가
script_path = Path(__file__).parent
project_root = script_path.parent
sys.path.append(str(project_root))

from sqlalchemy import create_engine, text
from app.core.config import settings

def reset_migrations():
    """
    마이그레이션 초기화
    1. alembic_version 삭제
    2. 모든 외래 키 제약 조건 삭제 (PostgreSQL 전용)
    3. 모든 테이블 삭제
    """
    try:
        # 데이터베이스 연결
        engine = create_engine(settings.DATABASE_URI)
        conn = engine.connect()
        
        # 트랜잭션 시작
        trans = conn.begin()
        
        try:
            # 1. alembic_version 초기화
            logger.info("alembic_version 테이블 초기화 중...")
            logger.info("alembic_version 테이블 초기화 중 (존재 시)...")
            try:
                conn.execute(text("DELETE FROM alembic_version"))
            except Exception as e:
                logger.warning(f"alembic_version 테이블이 없거나 삭제 실패: {e}")
            
            # 2. 모든 외래 키 제약 조건 삭제
            logger.info("모든 외래 키 제약 조건 삭제 중...")
            
            # PostgreSQL에서 모든 외래 키 제약 조건을 가져와 삭제
            result = conn.execute(text("""
                SELECT tc.table_name, tc.constraint_name
                FROM information_schema.table_constraints AS tc
                WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
            """))
            
            for row in result:
                table_name, constraint_name = row
                logger.info(f"테이블 {table_name}에서 외래 키 {constraint_name} 삭제 중...")
                conn.execute(text(f'ALTER TABLE "{table_name}" DROP CONSTRAINT "{constraint_name}"'))
            
            # 3. 모든 테이블 삭제 (alembic_version 제외)
            logger.info("모든 테이블 삭제 중...")
            enums_to_drop = ['badgetype', 'team_role_enum', 'paymentstatus', 'plantype','pointactiontype',]
            for enum in enums_to_drop:
                try:
                    conn.execute(text(f'DROP TYPE IF EXISTS {enum} CASCADE'))
                    logger.info(f"ENUM 타입 {enum} 삭제 완료")
                except Exception as e:
                    logger.warning(f"ENUM 타입 {enum} 삭제 중 오류: {str(e)}")
            
            # 테이블 목록 조회 (alembic_version 제외)
            result = conn.execute(text("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                AND tablename != 'alembic_version'
            """))
            
            # 테이블 삭제
            for row in result:
                table_name = row[0]
                logger.info(f"테이블 {table_name} 삭제 중...")
                conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
            
            # 트랜잭션 커밋
            trans.commit()
            logger.info("데이터베이스 초기화 완료")
            
        except Exception as e:
            # 트랜잭션 롤백
            trans.rollback()
            logger.error(f"데이터베이스 초기화 중 오류 발생: {str(e)}")
            raise
        finally:
            conn.close()
        
        return True
    except Exception as e:
        logger.error(f"데이터베이스 연결 오류: {str(e)}")
        return False

def create_new_migration():
    """
    새 마이그레이션 파일 생성
    """
    try:
        # alembic 설정 경로
        alembic_dir = project_root / "alembic"
        
        # 이전 마이그레이션 파일 백업
        migrations_dir = alembic_dir / "versions"
        backup_dir = alembic_dir / "versions_backup"
        
        if not backup_dir.exists():
            os.makedirs(backup_dir)
        
        # 기존 마이그레이션 파일 백업
        for file in migrations_dir.glob("*.py"):
            if file.is_file():
                target_file = backup_dir / file.name
                logger.info(f"마이그레이션 파일 백업 중: {file.name}")
                if not target_file.exists():
                    os.rename(file, target_file)
        
        # 새 마이그레이션 생성
        logger.info("새 마이그레이션 생성 중...")
        os.system(f"cd {project_root} && alembic revision --autogenerate -m 'recreate_all_tables'")
        
        logger.info("새 마이그레이션 생성 완료")
        return True
    except Exception as e:
        logger.error(f"마이그레이션 생성 중 오류 발생: {str(e)}")
        return False

def run_migration():
    """
    마이그레이션 실행
    """
    try:
        logger.info("마이그레이션 실행 중...")
        result = os.system(f"cd {project_root} && alembic upgrade head")
        
        if result == 0:
            logger.info("마이그레이션 성공적으로 실행됨")
            return True
        else:
            logger.error(f"마이그레이션 실행 실패, 반환 코드: {result}")
            return False
    except Exception as e:
        logger.error(f"마이그레이션 실행 중 오류 발생: {str(e)}")
        return False

def main():
    """
    메인 함수
    """
    logger.info("=== 마이그레이션 복구 스크립트 시작 ===")
    
    # 1. 마이그레이션 초기화
    logger.info("Step 1: 마이그레이션 초기화")
    if not reset_migrations():
        logger.error("마이그레이션 초기화 실패, 중단합니다.")
        return False
    
    # 2. 새 마이그레이션 생성
    logger.info("Step 2: 새 마이그레이션 생성")
    if not create_new_migration():
        logger.error("새 마이그레이션 생성 실패, 중단합니다.")
        return False
    
    # 3. 마이그레이션 실행
    logger.info("Step 3: 마이그레이션 실행")
    if not run_migration():
        logger.error("마이그레이션 실행 실패")
        return False
    
    logger.info("=== 마이그레이션 복구 스크립트 완료 ===")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)