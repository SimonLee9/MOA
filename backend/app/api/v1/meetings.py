"""
Meetings API endpoints
"""

from typing import Optional
from uuid import UUID
import math

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.meeting import (
    Meeting,
    MeetingSummary,
    Transcript,
    ActionItem,
    MeetingStatus as DBMeetingStatus,
)
from app.schemas.meeting import (
    MeetingCreate,
    MeetingUpdate,
    MeetingResponse,
    MeetingDetailResponse,
    MeetingSummaryResponse,
    MeetingSummaryUpdate,
    TranscriptSegment,
    TranscriptResponse,
    ActionItemResponse,
    ActionItemCreate,
    ActionItemUpdate,
    PaginatedResponse,
    ProcessingStatus,
)


router = APIRouter(prefix="/meetings", tags=["Meetings"])


# --- Meeting CRUD ---

@router.post("", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
async def create_meeting(
    meeting_data: MeetingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new meeting
    """
    meeting = Meeting(
        user_id=current_user.id,
        title=meeting_data.title,
        meeting_date=meeting_data.meeting_date,
        status=DBMeetingStatus.UPLOADED,
    )
    
    db.add(meeting)
    await db.commit()
    await db.refresh(meeting)
    
    return meeting


@router.get("", response_model=PaginatedResponse)
async def list_meetings(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of meetings for current user
    """
    # Base query
    query = select(Meeting).where(Meeting.user_id == current_user.id)
    
    # Filter by status if provided
    if status:
        try:
            status_enum = DBMeetingStatus(status)
            query = query.where(Meeting.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status: {status}"
            )
    
    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Paginate
    query = query.order_by(Meeting.created_at.desc())
    query = query.offset((page - 1) * size).limit(size)
    
    result = await db.execute(query)
    meetings = result.scalars().all()
    
    return PaginatedResponse(
        items=meetings,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total > 0 else 0,
    )


@router.get("/{meeting_id}", response_model=MeetingDetailResponse)
async def get_meeting(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get meeting details including summary, transcripts, and action items
    """
    result = await db.execute(
        select(Meeting)
        .options(
            selectinload(Meeting.summary),
            selectinload(Meeting.transcripts),
            selectinload(Meeting.action_items),
        )
        .where(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    return meeting


@router.patch("/{meeting_id}", response_model=MeetingResponse)
async def update_meeting(
    meeting_id: UUID,
    meeting_data: MeetingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update meeting details
    """
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == current_user.id
        )
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Update fields
    update_data = meeting_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(meeting, field, value)
    
    await db.commit()
    await db.refresh(meeting)
    
    return meeting


@router.delete("/{meeting_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_meeting(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a meeting and all related data
    """
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == current_user.id
        )
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    await db.delete(meeting)
    await db.commit()


# --- Processing Status ---

@router.get("/{meeting_id}/process/status", response_model=ProcessingStatus)
async def get_processing_status(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get the current processing status of a meeting
    """
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == current_user.id
        )
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Calculate progress based on status
    progress_map = {
        DBMeetingStatus.UPLOADED: 0,
        DBMeetingStatus.PROCESSING: 50,
        DBMeetingStatus.REVIEW_PENDING: 90,
        DBMeetingStatus.COMPLETED: 100,
        DBMeetingStatus.FAILED: 0,
    }
    
    step_map = {
        DBMeetingStatus.UPLOADED: "Waiting for processing",
        DBMeetingStatus.PROCESSING: "AI processing in progress",
        DBMeetingStatus.REVIEW_PENDING: "Waiting for human review",
        DBMeetingStatus.COMPLETED: "Completed",
        DBMeetingStatus.FAILED: "Failed",
    }
    
    return ProcessingStatus(
        meeting_id=meeting.id,
        status=meeting.status,
        progress=progress_map.get(meeting.status, 0),
        current_step=step_map.get(meeting.status),
        error_message=meeting.error_message if meeting.status == DBMeetingStatus.FAILED else None,
    )


# --- Summary ---

@router.get("/{meeting_id}/summary", response_model=MeetingSummaryResponse)
async def get_summary(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get meeting summary
    """
    result = await db.execute(
        select(Meeting)
        .options(selectinload(Meeting.summary))
        .where(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    if not meeting.summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not yet generated"
        )
    
    return meeting.summary


@router.put("/{meeting_id}/summary", response_model=MeetingSummaryResponse)
async def update_summary(
    meeting_id: UUID,
    summary_data: MeetingSummaryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update meeting summary (Human-in-the-Loop review)
    """
    result = await db.execute(
        select(Meeting)
        .options(selectinload(Meeting.summary))
        .where(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    if not meeting.summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Summary not yet generated"
        )
    
    # Update fields
    update_data = summary_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(meeting.summary, field, value)
    
    # If was pending review, mark as completed
    if meeting.status == DBMeetingStatus.REVIEW_PENDING:
        meeting.status = DBMeetingStatus.COMPLETED
    
    await db.commit()
    await db.refresh(meeting.summary)
    
    return meeting.summary


# --- Transcript ---

@router.get("/{meeting_id}/transcript", response_model=TranscriptResponse)
async def get_transcript(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get meeting transcript
    """
    result = await db.execute(
        select(Meeting)
        .options(selectinload(Meeting.transcripts))
        .where(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    if not meeting.transcripts:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transcript not yet generated"
        )
    
    # Get unique speakers
    speakers = set(t.speaker for t in meeting.transcripts)
    
    # Get total duration
    total_duration = max((t.end_time for t in meeting.transcripts), default=0)
    
    return TranscriptResponse(
        meeting_id=meeting.id,
        segments=[
            TranscriptSegment(
                speaker=t.speaker,
                text=t.text,
                start_time=t.start_time,
                end_time=t.end_time,
                confidence=t.confidence,
            )
            for t in meeting.transcripts
        ],
        total_duration=total_duration,
        speaker_count=len(speakers),
    )


# --- Action Items ---

@router.get("/{meeting_id}/actions", response_model=list[ActionItemResponse])
async def get_action_items(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get action items for a meeting
    """
    result = await db.execute(
        select(Meeting)
        .options(selectinload(Meeting.action_items))
        .where(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    return meeting.action_items


@router.post("/{meeting_id}/actions", response_model=ActionItemResponse, status_code=status.HTTP_201_CREATED)
async def create_action_item(
    meeting_id: UUID,
    action_data: ActionItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually add an action item to a meeting
    """
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == current_user.id
        )
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    action_item = ActionItem(
        meeting_id=meeting.id,
        **action_data.model_dump()
    )
    
    db.add(action_item)
    await db.commit()
    await db.refresh(action_item)
    
    return action_item


@router.put("/{meeting_id}/actions/{action_id}", response_model=ActionItemResponse)
async def update_action_item(
    meeting_id: UUID,
    action_id: UUID,
    action_data: ActionItemUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an action item
    """
    # Verify meeting ownership
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == current_user.id
        )
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Get action item
    result = await db.execute(
        select(ActionItem).where(
            ActionItem.id == action_id,
            ActionItem.meeting_id == meeting_id
        )
    )
    action_item = result.scalar_one_or_none()
    
    if not action_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action item not found"
        )
    
    # Update fields
    update_data = action_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(action_item, field, value)
    
    await db.commit()
    await db.refresh(action_item)
    
    return action_item


@router.delete("/{meeting_id}/actions/{action_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_action_item(
    meeting_id: UUID,
    action_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete an action item
    """
    # Verify meeting ownership
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == current_user.id
        )
    )
    meeting = result.scalar_one_or_none()
    
    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )
    
    # Get and delete action item
    result = await db.execute(
        select(ActionItem).where(
            ActionItem.id == action_id,
            ActionItem.meeting_id == meeting_id
        )
    )
    action_item = result.scalar_one_or_none()
    
    if not action_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Action item not found"
        )
    
    await db.delete(action_item)
    await db.commit()
