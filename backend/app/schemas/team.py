"""
Team-related Pydantic schemas
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class TeamRole(str, Enum):
    """Team member roles"""
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


# ============ Team Schemas ============

class TeamCreate(BaseModel):
    """Schema for creating a new team"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    slug: str = Field(..., min_length=1, max_length=100, pattern=r"^[a-z0-9-]+$")


class TeamUpdate(BaseModel):
    """Schema for updating a team"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None


class TeamMemberResponse(BaseModel):
    """Team member response schema"""
    id: UUID
    user_id: UUID
    user_email: str
    user_name: str
    role: TeamRole
    joined_at: datetime

    class Config:
        from_attributes = True


class TeamResponse(BaseModel):
    """Team response schema"""
    id: UUID
    name: str
    description: Optional[str]
    slug: str
    owner_id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    member_count: Optional[int] = None

    class Config:
        from_attributes = True


class TeamDetailResponse(TeamResponse):
    """Detailed team response with members"""
    members: List[TeamMemberResponse] = []


class TeamListResponse(BaseModel):
    """Paginated list of teams"""
    items: List[TeamResponse]
    total: int
    page: int
    size: int
    pages: int


# ============ Team Member Schemas ============

class TeamMemberAdd(BaseModel):
    """Schema for adding a member to team"""
    user_id: UUID
    role: TeamRole = TeamRole.MEMBER


class TeamMemberUpdate(BaseModel):
    """Schema for updating member role"""
    role: TeamRole


# ============ Team Invitation Schemas ============

class TeamInvitationCreate(BaseModel):
    """Schema for creating an invitation"""
    email: EmailStr
    role: TeamRole = TeamRole.MEMBER


class TeamInvitationResponse(BaseModel):
    """Team invitation response schema"""
    id: UUID
    team_id: UUID
    team_name: str
    email: str
    role: TeamRole
    invited_by_name: str
    expires_at: datetime
    created_at: datetime
    is_expired: bool

    class Config:
        from_attributes = True


class TeamInvitationAccept(BaseModel):
    """Schema for accepting an invitation"""
    token: str
