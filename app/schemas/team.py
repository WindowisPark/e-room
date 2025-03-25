# app/schemas/team.py
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

# 팀 스키마
class TeamBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)

class TeamCreate(TeamBase):
    pass

class TeamUpdate(TeamBase):
    pass

class TeamResponse(TeamBase):
    id: int
    owner_id: int
    created_at: datetime
    role: Optional[str] = None
    is_owner: Optional[bool] = None
    
    class Config:
        orm_mode = True

# 팀 멤버 스키마
class TeamMemberBase(BaseModel):
    user_id: int
    role: str = Field(..., pattern="^(owner|editor|viewer)$")

class TeamMemberCreate(TeamMemberBase):
    pass

class TeamMemberResponse(TeamMemberBase):
    id: int
    team_id: int
    username: str
    email: str
    joined_at: datetime
    
    class Config:
        orm_mode = True