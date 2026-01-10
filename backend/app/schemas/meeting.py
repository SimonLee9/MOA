"""
Meeting Pydantic schemas for request/response validation
"""

from datetime import datetime, date
from typing import Optional, List
from uuid import UUID
from enum import Enum

from pydantic import BaseModel, Field


# --- Enums ---

class MeetingStatus(str, Enum):
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    REVIEW_PENDING = "review_pending"


class ActionItemStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ActionItemPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# --- Transcript Schemas ---

class TranscriptSegment(BaseModel):
    """Single transcript segment"""
    speaker: str = Field(..., description="Speaker name or ID")
    text: str = Field(..., description="Spoken text")
    start_time: float = Field(..., ge=0, description="Start time in seconds")
    end_time: float = Field(..., ge=0, description="End time in seconds")
    confidence: Optional[float] = Field(None, ge=0, le=1, description="STT confidence")
    
    model_config = {"from_attributes": True}


class TranscriptResponse(BaseModel):
    """Full transcript response"""
    meeting_id: UUID
    segments: List[TranscriptSegment]
    total_duration: float
    speaker_count: int


# --- Action Item Schemas ---

class ActionItemBase(BaseModel):
    """Base action item fields"""
    content: str = Field(..., min_length=1, description="Task content")
    assignee: Optional[str] = Field(None, max_length=100, description="Assigned person")
    due_date: Optional[date] = Field(None, description="Due date")
    priority: ActionItemPriority = Field(
        default=ActionItemPriority.MEDIUM,
        description="Priority level"
    )


class ActionItemCreate(ActionItemBase):
    """Schema for creating action item"""
    pass


class ActionItemUpdate(BaseModel):
    """Schema for updating action item"""
    content: Optional[str] = Field(None, min_length=1)
    assignee: Optional[str] = Field(None, max_length=100)
    due_date: Optional[date] = None
    priority: Optional[ActionItemPriority] = None
    status: Optional[ActionItemStatus] = None


class ActionItemResponse(ActionItemBase):
    """Schema for action item response"""
    id: UUID
    meeting_id: UUID
    status: ActionItemStatus
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# --- Meeting Summary Schemas ---

class MeetingSummaryBase(BaseModel):
    """Base summary fields"""
    summary: str = Field(..., description="Full meeting summary")
    key_points: List[str] = Field(default_factory=list, description="Key discussion points")
    decisions: List[str] = Field(default_factory=list, description="Decisions made")


class MeetingSummaryUpdate(BaseModel):
    """Schema for updating summary (Human-in-the-Loop)"""
    summary: Optional[str] = None
    key_points: Optional[List[str]] = None
    decisions: Optional[List[str]] = None


class MeetingSummaryResponse(MeetingSummaryBase):
    """Schema for summary response"""
    id: UUID
    meeting_id: UUID
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


# --- Meeting Schemas ---

class MeetingBase(BaseModel):
    """Base meeting fields"""
    title: str = Field(..., min_length=1, max_length=255, description="Meeting title")
    meeting_date: Optional[date] = Field(None, description="Date of the meeting")
    tags: List[str] = Field(default_factory=list, description="Meeting tags for categorization")


class MeetingCreate(MeetingBase):
    """Schema for creating a meeting"""
    pass


class MeetingUpdate(BaseModel):
    """Schema for updating a meeting"""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    meeting_date: Optional[date] = None
    tags: Optional[List[str]] = None


class MeetingResponse(MeetingBase):
    """Schema for meeting response (list view)"""
    id: UUID
    user_id: UUID
    status: MeetingStatus
    audio_file_url: Optional[str] = None
    audio_duration: Optional[int] = Field(None, description="Duration in seconds")
    created_at: datetime
    updated_at: datetime
    
    model_config = {"from_attributes": True}


class MeetingDetailResponse(MeetingResponse):
    """Schema for meeting detail response (includes related data)"""
    summary: Optional[MeetingSummaryResponse] = None
    transcripts: Optional[List[TranscriptSegment]] = None
    action_items: Optional[List[ActionItemResponse]] = None
    error_message: Optional[str] = None


# --- Upload Response ---

class UploadResponse(BaseModel):
    """Response after file upload"""
    meeting_id: UUID
    audio_file_url: str
    audio_duration: Optional[int] = None
    status: MeetingStatus
    message: str


# --- Processing Status ---

class ProcessingStatus(BaseModel):
    """Response for processing status check"""
    meeting_id: UUID
    status: MeetingStatus
    progress: Optional[int] = Field(None, ge=0, le=100, description="Progress percentage")
    current_step: Optional[str] = None
    error_message: Optional[str] = None


# --- Pagination ---

class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    items: List[MeetingResponse]
    total: int
    page: int
    size: int
    pages: int
