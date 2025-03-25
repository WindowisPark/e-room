# app/models/team.py
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from app.db.base_class import Base

class Team(Base):
    """
    팀스페이스 모델
    """
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    created_at = Column(DateTime, default=datetime.utcnow)

    # 관계 설정
    owner = relationship("User", back_populates="owned_teams", foreign_keys=[owner_id])
    members = relationship("TeamMember", back_populates="team", cascade="all, delete-orphan")
    pdf_files = relationship("PDFFile", back_populates="team")

class TeamMember(Base):
    """
    팀 멤버십 모델
    """
    __tablename__ = "team_members"
    
    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id", ondelete="CASCADE"))
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    role = Column(Enum("owner", "editor", "viewer", name="team_role_enum"), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    # 관계 설정
    team = relationship("Team", back_populates="members")
    user = relationship("User", back_populates="team_memberships")