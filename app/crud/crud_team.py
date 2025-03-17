# app/crud/crud_team.py
from typing import List, Optional, Union, Dict, Any
from sqlalchemy.orm import Session
from app.models.team import Team, TeamMember
from app.models.user import User
from app.schemas.team import TeamCreate, TeamUpdate, TeamMemberCreate

def get_team_by_id(db: Session, team_id: int) -> Optional[Team]:
    """ID로 팀스페이스 조회"""
    return db.query(Team).filter(Team.id == team_id).first()

def get_teams_by_owner(db: Session, owner_id: int) -> List[Team]:
    """소유자 ID로 팀스페이스 목록 조회"""
    return db.query(Team).filter(Team.owner_id == owner_id).all()

def get_teams_by_user(db: Session, user_id: int) -> List[Team]:
    """사용자가 멤버로 속한 팀스페이스 목록 조회"""
    return db.query(Team).join(TeamMember).filter(TeamMember.user_id == user_id).all()

def create_team(db: Session, team_data: TeamCreate, owner_id: int) -> Team:
    """팀스페이스 생성"""
    db_team = Team(
        name=team_data.name,
        owner_id=owner_id
    )
    db.add(db_team)
    db.commit()
    db.refresh(db_team)
    
    # 소유자를 자동으로 멤버로 추가
    db_member = TeamMember(
        team_id=db_team.id,
        user_id=owner_id,
        role="owner"
    )
    db.add(db_member)
    db.commit()
    
    return db_team

def update_team(db: Session, team_id: int, team_data: TeamUpdate, owner_id: int) -> Optional[Team]:
    """팀스페이스 업데이트 (소유자만 가능)"""
    db_team = get_team_by_id(db, team_id)
    if not db_team or db_team.owner_id != owner_id:
        return None
    
    for key, value in team_data.dict(exclude_unset=True).items():
        setattr(db_team, key, value)
    
    db.commit()
    db.refresh(db_team)
    return db_team

def delete_team(db: Session, team_id: int, owner_id: int) -> bool:
    """팀스페이스 삭제 (소유자만 가능)"""
    db_team = get_team_by_id(db, team_id)
    if not db_team or db_team.owner_id != owner_id:
        return False
    
    db.delete(db_team)
    db.commit()
    return True

def add_team_member(db: Session, team_id: int, member_data: TeamMemberCreate, admin_id: int) -> Optional[TeamMember]:
    """팀스페이스 멤버 추가 (팀 소유자만 가능)"""
    # 팀 존재 및 요청자 권한 확인
    db_team = get_team_by_id(db, team_id)
    if not db_team or db_team.owner_id != admin_id:
        return None
    
    # 사용자 존재 확인
    user = db.query(User).filter(User.id == member_data.user_id).first()
    if not user:
        return None
    
    # 이미 멤버인지 확인
    existing_member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id, 
        TeamMember.user_id == member_data.user_id
    ).first()
    
    if existing_member:
        # 이미 멤버라면 역할만 업데이트
        existing_member.role = member_data.role
        db.commit()
        db.refresh(existing_member)
        return existing_member
    
    # 새 멤버 추가
    db_member = TeamMember(
        team_id=team_id,
        user_id=member_data.user_id,
        role=member_data.role
    )
    db.add(db_member)
    db.commit()
    db.refresh(db_member)
    return db_member

def remove_team_member(db: Session, team_id: int, user_id: int, admin_id: int) -> bool:
    """팀스페이스 멤버 제거 (팀 소유자만 가능)"""
    # 팀 존재 및 요청자 권한 확인
    db_team = get_team_by_id(db, team_id)
    if not db_team or db_team.owner_id != admin_id:
        return False
    
    # 소유자는 제거할 수 없음
    if user_id == db_team.owner_id:
        return False
    
    # 멤버 찾기 및 제거
    db_member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id, 
        TeamMember.user_id == user_id
    ).first()
    
    if not db_member:
        return False
    
    db.delete(db_member)
    db.commit()
    return True

def check_user_in_team(db: Session, team_id: int, user_id: int) -> bool:
    """사용자가 팀의 멤버인지 확인"""
    # 팀 소유자 확인
    db_team = get_team_by_id(db, team_id)
    if db_team and db_team.owner_id == user_id:
        return True
    
    # 팀 멤버 확인
    db_member = db.query(TeamMember).filter(
        TeamMember.team_id == team_id, 
        TeamMember.user_id == user_id
    ).first()
    
    return db_member is not None

def get_team_members(db: Session, team_id: int) -> List[Dict[str, Any]]:
    """팀스페이스 멤버 목록 조회"""
    members = (
        db.query(TeamMember, User)
        .join(User, TeamMember.user_id == User.id)
        .filter(TeamMember.team_id == team_id)
        .all()
    )
    
    result = []
    for member, user in members:
        result.append({
            "user_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": member.role,
            "joined_at": member.joined_at
        })
    
    return result