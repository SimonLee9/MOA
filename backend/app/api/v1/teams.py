"""
Teams API endpoints
Handles team creation, membership, and collaboration features
"""

import math
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.team import Team, TeamMember, TeamInvitation, TeamRole
from app.schemas.team import (
    TeamCreate,
    TeamUpdate,
    TeamResponse,
    TeamDetailResponse,
    TeamListResponse,
    TeamMemberAdd,
    TeamMemberUpdate,
    TeamMemberResponse,
    TeamInvitationCreate,
    TeamInvitationResponse,
    TeamInvitationAccept,
)


router = APIRouter(prefix="/teams", tags=["Teams"])


# ============ Team CRUD ============

@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new team.
    The current user becomes the owner automatically.
    """
    # Check if slug is unique
    existing = await db.execute(
        select(Team).where(Team.slug == team_data.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Team with this slug already exists"
        )

    # Create team
    team = Team(
        name=team_data.name,
        description=team_data.description,
        slug=team_data.slug,
        owner_id=current_user.id,
    )
    db.add(team)
    await db.flush()

    # Add owner as member with OWNER role
    owner_member = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        role=TeamRole.OWNER,
    )
    db.add(owner_member)

    await db.commit()
    await db.refresh(team)

    return TeamResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        slug=team.slug,
        owner_id=team.owner_id,
        is_active=team.is_active,
        created_at=team.created_at,
        updated_at=team.updated_at,
        member_count=1,
    )


@router.get("", response_model=TeamListResponse)
async def list_teams(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of teams the current user is a member of.
    """
    # Base query - teams where user is a member
    base_query = (
        select(Team)
        .join(TeamMember, Team.id == TeamMember.team_id)
        .where(TeamMember.user_id == current_user.id)
        .where(Team.is_active == True)
    )

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get teams with pagination
    query = base_query.order_by(Team.created_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    teams = result.scalars().all()

    # Get member counts
    team_responses = []
    for team in teams:
        count_result = await db.execute(
            select(func.count()).where(TeamMember.team_id == team.id)
        )
        member_count = count_result.scalar()
        team_responses.append(TeamResponse(
            id=team.id,
            name=team.name,
            description=team.description,
            slug=team.slug,
            owner_id=team.owner_id,
            is_active=team.is_active,
            created_at=team.created_at,
            updated_at=team.updated_at,
            member_count=member_count,
        ))

    return TeamListResponse(
        items=team_responses,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 0,
    )


@router.get("/{team_id}", response_model=TeamDetailResponse)
async def get_team(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get team details including members.
    User must be a member of the team.
    """
    # Check membership
    member_result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id
        )
    )
    if not member_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team"
        )

    # Get team with members
    result = await db.execute(
        select(Team)
        .options(selectinload(Team.members))
        .where(Team.id == team_id)
    )
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Build member responses with user info
    member_responses = []
    for member in team.members:
        user_result = await db.execute(
            select(User).where(User.id == member.user_id)
        )
        user = user_result.scalar_one()
        member_responses.append(TeamMemberResponse(
            id=member.id,
            user_id=member.user_id,
            user_email=user.email,
            user_name=user.name,
            role=member.role,
            joined_at=member.joined_at,
        ))

    return TeamDetailResponse(
        id=team.id,
        name=team.name,
        description=team.description,
        slug=team.slug,
        owner_id=team.owner_id,
        is_active=team.is_active,
        created_at=team.created_at,
        updated_at=team.updated_at,
        member_count=len(member_responses),
        members=member_responses,
    )


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: UUID,
    team_data: TeamUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update team details.
    Only owner or admin can update.
    """
    # Check permission
    member_result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id,
            TeamMember.role.in_([TeamRole.OWNER, TeamRole.ADMIN])
        )
    )
    if not member_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner or admin can update team"
        )

    # Get and update team
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    update_data = team_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(team, field, value)

    await db.commit()
    await db.refresh(team)

    return team


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a team.
    Only owner can delete.
    """
    result = await db.execute(select(Team).where(Team.id == team_id))
    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    if team.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only team owner can delete the team"
        )

    await db.delete(team)
    await db.commit()


# ============ Team Members ============

@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
async def add_team_member(
    team_id: UUID,
    member_data: TeamMemberAdd,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add a member to the team.
    Only owner or admin can add members.
    """
    # Check permission
    member_result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id,
            TeamMember.role.in_([TeamRole.OWNER, TeamRole.ADMIN])
        )
    )
    if not member_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner or admin can add members"
        )

    # Check if user exists
    user_result = await db.execute(
        select(User).where(User.id == member_data.user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Check if already a member
    existing = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == member_data.user_id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member of this team"
        )

    # Cannot assign OWNER role
    if member_data.role == TeamRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot assign owner role. Transfer ownership instead."
        )

    # Add member
    new_member = TeamMember(
        team_id=team_id,
        user_id=member_data.user_id,
        role=member_data.role,
    )
    db.add(new_member)
    await db.commit()
    await db.refresh(new_member)

    return TeamMemberResponse(
        id=new_member.id,
        user_id=new_member.user_id,
        user_email=user.email,
        user_name=user.name,
        role=new_member.role,
        joined_at=new_member.joined_at,
    )


@router.patch("/{team_id}/members/{user_id}", response_model=TeamMemberResponse)
async def update_member_role(
    team_id: UUID,
    user_id: UUID,
    update_data: TeamMemberUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update a member's role.
    Only owner or admin can update roles.
    """
    # Check permission
    current_member_result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id,
            TeamMember.role.in_([TeamRole.OWNER, TeamRole.ADMIN])
        )
    )
    current_member = current_member_result.scalar_one_or_none()
    if not current_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner or admin can update member roles"
        )

    # Get target member
    target_result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        )
    )
    target_member = target_result.scalar_one_or_none()
    if not target_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    # Cannot change owner's role
    if target_member.role == TeamRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change owner's role. Transfer ownership instead."
        )

    # Admin cannot assign OWNER or ADMIN role
    if current_member.role == TeamRole.ADMIN and update_data.role in [TeamRole.OWNER, TeamRole.ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin cannot assign owner or admin role"
        )

    target_member.role = update_data.role
    await db.commit()
    await db.refresh(target_member)

    # Get user info
    user_result = await db.execute(select(User).where(User.id == user_id))
    user = user_result.scalar_one()

    return TeamMemberResponse(
        id=target_member.id,
        user_id=target_member.user_id,
        user_email=user.email,
        user_name=user.name,
        role=target_member.role,
        joined_at=target_member.joined_at,
    )


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a member from the team.
    Owner/Admin can remove others, members can remove themselves.
    """
    # Get target member
    target_result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id
        )
    )
    target_member = target_result.scalar_one_or_none()
    if not target_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found"
        )

    # Owner cannot be removed
    if target_member.role == TeamRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Owner cannot be removed. Transfer ownership first."
        )

    # Check permission
    if user_id != current_user.id:
        # Must be owner or admin to remove others
        current_member_result = await db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == current_user.id,
                TeamMember.role.in_([TeamRole.OWNER, TeamRole.ADMIN])
            )
        )
        if not current_member_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only owner or admin can remove other members"
            )

    await db.delete(target_member)
    await db.commit()


# ============ Team Invitations ============

@router.post("/{team_id}/invitations", response_model=TeamInvitationResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation(
    team_id: UUID,
    invitation_data: TeamInvitationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create an invitation to join the team.
    Only owner or admin can invite.
    """
    # Check permission
    member_result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id,
            TeamMember.role.in_([TeamRole.OWNER, TeamRole.ADMIN])
        )
    )
    if not member_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner or admin can invite members"
        )

    # Get team
    team_result = await db.execute(select(Team).where(Team.id == team_id))
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found"
        )

    # Check if email is already a member
    user_result = await db.execute(
        select(User).where(User.email == invitation_data.email)
    )
    existing_user = user_result.scalar_one_or_none()
    if existing_user:
        existing_member = await db.execute(
            select(TeamMember).where(
                TeamMember.team_id == team_id,
                TeamMember.user_id == existing_user.id
            )
        )
        if existing_member.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User is already a member of this team"
            )

    # Create invitation
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)

    invitation = TeamInvitation(
        team_id=team_id,
        email=invitation_data.email,
        role=invitation_data.role,
        invited_by_id=current_user.id,
        token=token,
        expires_at=expires_at,
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    return TeamInvitationResponse(
        id=invitation.id,
        team_id=invitation.team_id,
        team_name=team.name,
        email=invitation.email,
        role=invitation.role,
        invited_by_name=current_user.name,
        expires_at=invitation.expires_at,
        created_at=invitation.created_at,
        is_expired=invitation.is_expired,
    )


@router.get("/invitations/pending", response_model=list[TeamInvitationResponse])
async def get_pending_invitations(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get pending invitations for the current user's email.
    """
    result = await db.execute(
        select(TeamInvitation)
        .options(selectinload(TeamInvitation.team))
        .where(
            TeamInvitation.email == current_user.email,
            TeamInvitation.accepted_at == None
        )
    )
    invitations = result.scalars().all()

    responses = []
    for inv in invitations:
        inviter_result = await db.execute(
            select(User).where(User.id == inv.invited_by_id)
        )
        inviter = inviter_result.scalar_one()
        responses.append(TeamInvitationResponse(
            id=inv.id,
            team_id=inv.team_id,
            team_name=inv.team.name,
            email=inv.email,
            role=inv.role,
            invited_by_name=inviter.name,
            expires_at=inv.expires_at,
            created_at=inv.created_at,
            is_expired=inv.is_expired,
        ))

    return responses


@router.post("/invitations/accept", response_model=TeamMemberResponse)
async def accept_invitation(
    accept_data: TeamInvitationAccept,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Accept a team invitation.
    """
    # Find invitation
    result = await db.execute(
        select(TeamInvitation).where(TeamInvitation.token == accept_data.token)
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    # Check if invitation is for current user
    if invitation.email != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This invitation is not for you"
        )

    # Check if expired
    if invitation.is_expired:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired"
        )

    # Check if already accepted
    if invitation.is_accepted:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has already been accepted"
        )

    # Check if already a member
    existing = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == invitation.team_id,
            TeamMember.user_id == current_user.id
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You are already a member of this team"
        )

    # Create membership
    new_member = TeamMember(
        team_id=invitation.team_id,
        user_id=current_user.id,
        role=invitation.role,
    )
    db.add(new_member)

    # Mark invitation as accepted
    invitation.accepted_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(new_member)

    return TeamMemberResponse(
        id=new_member.id,
        user_id=new_member.user_id,
        user_email=current_user.email,
        user_name=current_user.name,
        role=new_member.role,
        joined_at=new_member.joined_at,
    )


@router.delete("/{team_id}/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_invitation(
    team_id: UUID,
    invitation_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a pending invitation.
    Only owner or admin can cancel.
    """
    # Check permission
    member_result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == current_user.id,
            TeamMember.role.in_([TeamRole.OWNER, TeamRole.ADMIN])
        )
    )
    if not member_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner or admin can cancel invitations"
        )

    # Get invitation
    result = await db.execute(
        select(TeamInvitation).where(
            TeamInvitation.id == invitation_id,
            TeamInvitation.team_id == team_id
        )
    )
    invitation = result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found"
        )

    await db.delete(invitation)
    await db.commit()
