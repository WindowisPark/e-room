# app/services/team_service.py
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.crud.crud_team import (
    create_team, 
    update_team, 
    delete_team, 
    add_team_member, 
    remove_team_member,
    get_team_by_id,
    get_teams_by_user,
    get_team_members
)
from app.services.notification_service import create_team_invitation_notification
from app.schemas.team import TeamCreate, TeamUpdate, TeamMemberCreate

async def create_new_team(db: Session, team_data: TeamCreate, owner_id: int) -> Dict[str, Any]:
    """새 팀스페이스 생성"""
    # 팀 생성
    team = create_team(db=db, team_data=team_data, owner_id=owner_id)
    
    return {
        "id": team.id,
        "name": team.name,
        "owner_id": team.owner_id,
        "created_at": team.created_at
    }

async def update_team_info(db: Session, team_id: int, team_data: TeamUpdate, owner_id: int) -> Optional[Dict[str, Any]]:
    """팀스페이스 정보 업데이트"""
    updated_team = update_team(db=db, team_id=team_id, team_data=team_data, owner_id=owner_id)
    
    if not updated_team:
        return None
    
    return {
        "id": updated_team.id,
        "name": updated_team.name,
        "owner_id": updated_team.owner_id,
        "created_at": updated_team.created_at
    }

async def delete_team_space(db: Session, team_id: int, owner_id: int) -> bool:
    """팀스페이스 삭제"""
    return delete_team(db=db, team_id=team_id, owner_id=owner_id)

async def invite_team_member(db: Session, team_id: int, user_id: int, role: str, admin_id: int) -> Optional[Dict[str, Any]]:
    """팀에 새 멤버 초대"""
    # 팀 정보 조회
    team = get_team_by_id(db=db, team_id=team_id)
    if not team:
        return None
    
    # 멤버 추가
    member_data = TeamMemberCreate(user_id=user_id, role=role)
    member = add_team_member(db=db, team_id=team_id, member_data=member_data, admin_id=admin_id)
    
    if not member:
        return None
    
    # 초대 알림 생성
    await create_team_invitation_notification(
        db=db,
        team_id=team_id,
        team_name=team.name,
        inviter_id=admin_id,
        invitee_id=user_id
    )
    
    return {
        "team_id": team_id,
        "user_id": user_id,
        "role": member.role,
        "joined_at": member.joined_at
    }

async def remove_member_from_team(db: Session, team_id: int, user_id: int, admin_id: int) -> bool:
    """팀에서 멤버 제거"""
    return remove_team_member(db=db, team_id=team_id, user_id=user_id, admin_id=admin_id)

async def get_user_teams(db: Session, user_id: int) -> List[Dict[str, Any]]:
    """사용자가 속한 모든 팀스페이스 조회"""
    teams = get_teams_by_user(db=db, user_id=user_id)
    
    result = []
    for team in teams:
        # 사용자의 역할 확인
        is_owner = team.owner_id == user_id
        role = "owner" if is_owner else next(
            (member.role for member in team.members if member.user_id == user_id),
            "viewer"  # 기본값
        )
        
        result.append({
            "id": team.id,
            "name": team.name,
            "owner_id": team.owner_id,
            "created_at": team.created_at,
            "role": role,
            "is_owner": is_owner
        })
    
    return result

async def get_team_member_list(db: Session, team_id: int) -> List[Dict[str, Any]]:
    """팀스페이스 멤버 목록 조회"""
    return get_team_members(db=db, team_id=team_id)

async def check_team_permission(db: Session, team_id: int, user_id: int, required_role: str = "viewer") -> bool:
    """사용자가 팀에서 특정 역할 이상의 권한을 가지고 있는지 확인"""
    team = get_team_by_id(db=db, team_id=team_id)
    if not team:
        return False
    
    # 소유자는 항상 모든 권한을 가짐
    if team.owner_id == user_id:
        return True
    
    # 사용자의 역할 확인
    member_role = next(
        (member.role for member in team.members if member.user_id == user_id),
        None
    )
    
    if not member_role:
        return False
    
    # 역할 권한 체크
    role_hierarchy = {
        "owner": 3,
        "editor": 2,
        "viewer": 1
    }
    
    required_level = role_hierarchy.get(required_role, 0)
    user_level = role_hierarchy.get(member_role, 0)
    
    return user_level >= required_level