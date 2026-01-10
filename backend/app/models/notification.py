"""
Notification model for in-app notifications
"""

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from enum import Enum
import uuid

from sqlalchemy import String, DateTime, Text, ForeignKey, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.meeting import Meeting


class NotificationType(str, Enum):
    """Types of notifications"""
    REVIEW_PENDING = "review_pending"          # Meeting needs human review
    PROCESSING_COMPLETE = "processing_complete"  # Processing finished
    PROCESSING_FAILED = "processing_failed"    # Processing failed
    ACTION_DUE_SOON = "action_due_soon"        # Action item due soon
    ACTION_OVERDUE = "action_overdue"          # Action item overdue
    SYSTEM = "system"                          # System announcement


class Notification(Base):
    """In-app notification model"""

    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False
    )
    meeting_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("meetings.id", ondelete="CASCADE"),
        nullable=True
    )
    type: Mapped[NotificationType] = mapped_column(
        String(50),
        nullable=False
    )
    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False
    )
    message: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="notifications"
    )
    meeting: Mapped[Optional["Meeting"]] = relationship(
        "Meeting",
        back_populates="notifications"
    )

    def __repr__(self) -> str:
        return f"<Notification {self.type.value} for user {self.user_id}>"
