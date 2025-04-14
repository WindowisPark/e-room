# app/api/v1/endpoints/teams.py
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.subscription_service import check_team_creation_permission
from app.schemas.team import TeamCreate, TeamOwnerLeaveRequest, TeamUpdate, TeamResponse, TeamMemberCreate, TeamMemberResponse
from app.services.team_service import (
    create_new_team,
    get_team_by_id_and_user,
    owner_leave_team,
    update_team_info,
    delete_team_space,
    invite_team_member,
    remove_member_from_team,
    get_user_teams,
    get_team_member_list,
    check_team_permission
)

router = APIRouter()

async def ensure_team_access(team_id: int, user: User, db: Session):
    has_access = await check_team_permission(db=db, team_id=team_id, user_id=user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 팀스페이스에 접근할 권한이 없습니다"
        )
    
@router.post("/", response_model=TeamResponse)
async def create_team(
    team_data: TeamCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """팀스페이스 생성 (구독 권한 확인)"""
    
    # 팀 생성 권한 확인
    has_permission = await check_team_creation_permission(db, current_user.id)
    if not has_permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="팀스페이스 생성 권한이 없습니다. 구독 요금제를 확인해주세요."
        )
    
    # 기존 로직 유지
    result = await create_new_team(db=db, team_data=team_data, owner_id=current_user.id)
    
    # 포인트 적립
    from app.services.point_service import add_points, PointActionType
    
    await add_points(
        db=db,
        user_id=current_user.id,
        action_type=PointActionType.TEAM_CREATE,
        description=f"팀스페이스 생성: {team_data.name}",
        reference_id=result.get("id")
    )

@router.get("/", response_model=List[TeamResponse])
async def get_teams(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """사용자가 속한 팀스페이스 목록 조회"""
    teams = await get_user_teams(db=db, user_id=current_user.id)
    return teams

@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """팀스페이스 상세 정보 조회"""
    await ensure_team_access(team_id, current_user, db)

    team = await get_team_by_id_and_user(db=db, team_id=team_id, user_id=current_user.id)
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="팀스페이스를 찾을 수 없습니다"
        )
    return team

@router.put("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_data: TeamUpdate,
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """팀스페이스 정보 업데이트 (소유자만 가능)"""
    result = await update_team_info(
        db=db, 
        team_id=team_id, 
        team_data=team_data, 
        owner_id=current_user.id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="팀스페이스를 수정할 권한이 없습니다"
        )
    
    return result

@router.delete("/{team_id}")
async def delete_team(
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """팀스페이스 삭제 (소유자만 가능)"""
    success = await delete_team_space(
        db=db, 
        team_id=team_id, 
        owner_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="팀스페이스를 삭제할 권한이 없습니다"
        )
    
    return {"message": "팀스페이스가 삭제되었습니다"}

@router.get("/{team_id}/members", response_model=List[TeamMemberResponse])
async def get_members(
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """팀스페이스 멤버 목록 조회"""
    # 팀 멤버십 확인
    has_access = await check_team_permission(db=db, team_id=team_id, user_id=current_user.id)
    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="이 팀스페이스의 멤버 목록을 조회할 권한이 없습니다"
        )
    
    members = await get_team_member_list(db=db, team_id=team_id)
    return members

@router.post("/{team_id}/members", response_model=TeamMemberResponse)
async def invite_member(
    member_data: TeamMemberCreate,
    team_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """팀스페이스 멤버 초대 (소유자만 가능)"""
    result = await invite_team_member(
        db=db,
        team_id=team_id,
        user_id=member_data.user_id,
        role=member_data.role,
        admin_id=current_user.id
    )
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="멤버를 초대할 권한이 없거나 유효하지 않은 사용자입니다"
        )
    
    return result

@router.delete("/{team_id}/members/{user_id}")
async def remove_member(
    team_id: int = Path(..., ge=1),
    user_id: int = Path(..., ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """팀스페이스 멤버 제거 (소유자만 가능)"""
    success = await remove_member_from_team(
        db=db, 
        team_id=team_id, 
        user_id=user_id, 
        admin_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="멤버를 제거할 권한이 없거나 유효하지 않은 요청입니다"
        )
    
    return {"message": "멤버가 제거되었습니다"}

@router.post("/{team_id}/owner-leave")
async def leave_team_as_owner(
    team_id: int = Path(..., ge=1),
    req: TeamOwnerLeaveRequest = ...,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """방장이 팀스페이스를 떠날 때: 위임 or 삭제 선택"""
    success = await owner_leave_team(
        db=db,
        team_id=team_id,
        owner_id=current_user.id,
        action=req.action,
        new_owner_id=req.new_owner_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="처리를 완료할 수 없습니다. 권한 또는 요청을 확인하세요."
        )

    return {
        "message": "팀스페이스를 떠났습니다." if req.action == "transfer"
                   else "팀스페이스가 삭제되었습니다."
    }
