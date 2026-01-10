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
    query_str: Optional[str] = Query(None, alias="q", description="Search in title"),
    date_from: Optional[str] = Query(None, description="Filter from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Filter to date (YYYY-MM-DD)"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    sort_by: str = Query("created_at", description="Sort field: created_at, meeting_date, title"),
    sort_order: str = Query("desc", description="Sort order: asc, desc"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of meetings for current user with search and filter options

    - **q**: Search query for title (case-insensitive partial match)
    - **status**: Filter by meeting status
    - **date_from**: Filter meetings from this date
    - **date_to**: Filter meetings until this date
    - **tag**: Filter by tag
    - **sort_by**: Sort by field (created_at, meeting_date, title)
    - **sort_order**: Sort order (asc, desc)
    """
    from datetime import datetime

    # Base query
    base_query = select(Meeting).where(Meeting.user_id == current_user.id)

    # Filter by status if provided
    if status:
        try:
            status_enum = DBMeetingStatus(status)
            base_query = base_query.where(Meeting.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}"
            )

    # Search by title (case-insensitive)
    if query_str:
        base_query = base_query.where(Meeting.title.ilike(f"%{query_str}%"))

    # Filter by tag
    if tag:
        base_query = base_query.where(Meeting.tags.contains([tag]))

    # Filter by date range
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            base_query = base_query.where(Meeting.meeting_date >= from_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date_from format. Use YYYY-MM-DD"
            )

    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            base_query = base_query.where(Meeting.meeting_date <= to_date)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid date_to format. Use YYYY-MM-DD"
            )

    # Count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Validate and apply sorting
    valid_sort_fields = {"created_at", "meeting_date", "title"}
    if sort_by not in valid_sort_fields:
        sort_by = "created_at"

    sort_column = getattr(Meeting, sort_by)
    if sort_order.lower() == "asc":
        base_query = base_query.order_by(sort_column.asc())
    else:
        base_query = base_query.order_by(sort_column.desc())

    # Paginate
    base_query = base_query.offset((page - 1) * size).limit(size)

    result = await db.execute(base_query)
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


# --- Tags Management ---

@router.get("/tags/list")
async def list_all_tags(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all unique tags used by the current user
    """
    result = await db.execute(
        select(Meeting.tags)
        .where(Meeting.user_id == current_user.id)
        .where(Meeting.tags != None)
    )

    all_tags = set()
    for row in result.all():
        if row.tags:
            all_tags.update(row.tags)

    return {"tags": sorted(list(all_tags))}


@router.post("/{meeting_id}/tags")
async def add_tags(
    meeting_id: UUID,
    tags: list[str],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add tags to a meeting
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

    # Add new tags (avoid duplicates)
    current_tags = set(meeting.tags or [])
    current_tags.update(tags)
    meeting.tags = list(current_tags)

    await db.commit()
    await db.refresh(meeting)

    return {"tags": meeting.tags}


@router.delete("/{meeting_id}/tags/{tag}")
async def remove_tag(
    meeting_id: UUID,
    tag: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove a tag from a meeting
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

    if meeting.tags and tag in meeting.tags:
        meeting.tags = [t for t in meeting.tags if t != tag]
        await db.commit()
        await db.refresh(meeting)

    return {"tags": meeting.tags or []}
