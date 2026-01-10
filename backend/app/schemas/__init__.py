"""
Pydantic Schemas
"""

from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserUpdate,
    UserResponse,
    TokenResponse,
    TokenPayload,
)
from app.schemas.meeting import (
    MeetingStatus,
    ActionItemStatus,
    ActionItemPriority,
    TranscriptSegment,
    TranscriptResponse,
    ActionItemBase,
    ActionItemCreate,
    ActionItemUpdate,
    ActionItemResponse,
    MeetingSummaryBase,
    MeetingSummaryUpdate,
    MeetingSummaryResponse,
    MeetingBase,
    MeetingCreate,
    MeetingUpdate,
    MeetingResponse,
    MeetingDetailResponse,
    UploadResponse,
    ProcessingStatus,
    PaginatedResponse,
)

__all__ = [
    # User
    "UserCreate",
    "UserLogin",
    "UserUpdate",
    "UserResponse",
    "TokenResponse",
    "TokenPayload",
    # Meeting
    "MeetingStatus",
    "ActionItemStatus",
    "ActionItemPriority",
    "TranscriptSegment",
    "TranscriptResponse",
    "ActionItemBase",
    "ActionItemCreate",
    "ActionItemUpdate",
    "ActionItemResponse",
    "MeetingSummaryBase",
    "MeetingSummaryUpdate",
    "MeetingSummaryResponse",
    "MeetingBase",
    "MeetingCreate",
    "MeetingUpdate",
    "MeetingResponse",
    "MeetingDetailResponse",
    "UploadResponse",
    "ProcessingStatus",
    "PaginatedResponse",
]
