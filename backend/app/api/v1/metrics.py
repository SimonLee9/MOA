"""
Metrics and Monitoring API
Provides endpoints for system health and workflow metrics
"""

from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.meeting import Meeting, MeetingStatus


router = APIRouter(prefix="/metrics", tags=["Metrics"])


# === Response Models ===


class SystemHealth(BaseModel):
    """System health status"""
    status: str  # healthy, degraded, unhealthy
    database: str
    redis: str
    ai_pipeline: str
    timestamp: str


class WorkflowMetrics(BaseModel):
    """Workflow processing metrics"""
    total_meetings: int
    processing: int
    completed: int
    failed: int
    pending_review: int
    avg_processing_time_seconds: Optional[float]
    success_rate: float


class DailyStats(BaseModel):
    """Daily statistics"""
    date: str
    meetings_created: int
    meetings_completed: int
    meetings_failed: int


class UserMetrics(BaseModel):
    """User-specific metrics"""
    total_meetings: int
    completed_meetings: int
    pending_review: int
    total_action_items: int
    completed_action_items: int


# === Endpoints ===


@router.get("/health", response_model=SystemHealth)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    System health check endpoint

    Checks the status of:
    - Database connection
    - Redis connection
    - AI Pipeline availability
    """
    health = {
        "database": "unknown",
        "redis": "unknown",
        "ai_pipeline": "unknown",
    }

    # Check database
    try:
        await db.execute(select(func.now()))
        health["database"] = "healthy"
    except Exception as e:
        health["database"] = f"unhealthy: {str(e)[:50]}"

    # Check Redis
    try:
        import redis.asyncio as redis
        from app.config import get_settings
        settings = get_settings()
        r = redis.from_url(settings.redis_url)
        await r.ping()
        await r.close()
        health["redis"] = "healthy"
    except Exception as e:
        health["redis"] = f"unhealthy: {str(e)[:50]}"

    # Check AI Pipeline
    try:
        from ai_pipeline.pipeline.checkpointer import get_checkpointer
        checkpointer = await get_checkpointer()
        health["ai_pipeline"] = "healthy"
    except Exception as e:
        health["ai_pipeline"] = f"unhealthy: {str(e)[:50]}"

    # Determine overall status
    statuses = list(health.values())
    if all(s == "healthy" for s in statuses):
        overall_status = "healthy"
    elif any("unhealthy" in s for s in statuses):
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"

    return SystemHealth(
        status=overall_status,
        database=health["database"],
        redis=health["redis"],
        ai_pipeline=health["ai_pipeline"],
        timestamp=datetime.utcnow().isoformat(),
    )


@router.get("/workflows", response_model=WorkflowMetrics)
async def get_workflow_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get workflow processing metrics

    Returns overall statistics about meeting processing.
    """
    # Count meetings by status
    result = await db.execute(
        select(
            Meeting.status,
            func.count(Meeting.id).label("count"),
        )
        .where(Meeting.user_id == current_user.id)
        .group_by(Meeting.status)
    )

    status_counts = {row.status: row.count for row in result.all()}

    total = sum(status_counts.values())
    processing = status_counts.get(MeetingStatus.PROCESSING, 0)
    completed = status_counts.get(MeetingStatus.COMPLETED, 0)
    failed = status_counts.get(MeetingStatus.FAILED, 0)
    pending_review = status_counts.get(MeetingStatus.REVIEW_PENDING, 0)

    # Calculate success rate
    finished = completed + failed
    success_rate = (completed / finished * 100) if finished > 0 else 0.0

    # Calculate average processing time (for completed meetings)
    result = await db.execute(
        select(
            func.avg(
                func.extract(
                    'epoch',
                    Meeting.updated_at - Meeting.created_at
                )
            ).label("avg_time")
        )
        .where(
            and_(
                Meeting.user_id == current_user.id,
                Meeting.status == MeetingStatus.COMPLETED,
            )
        )
    )
    avg_time = result.scalar()

    return WorkflowMetrics(
        total_meetings=total,
        processing=processing,
        completed=completed,
        failed=failed,
        pending_review=pending_review,
        avg_processing_time_seconds=avg_time,
        success_rate=round(success_rate, 2),
    )


@router.get("/daily", response_model=List[DailyStats])
async def get_daily_stats(
    days: int = 7,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get daily meeting statistics

    Returns meeting counts for the last N days.
    """
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=days - 1)

    # Get created counts by date
    created_result = await db.execute(
        select(
            func.date(Meeting.created_at).label("date"),
            func.count(Meeting.id).label("count"),
        )
        .where(
            and_(
                Meeting.user_id == current_user.id,
                func.date(Meeting.created_at) >= start_date,
            )
        )
        .group_by(func.date(Meeting.created_at))
    )
    created_by_date = {str(row.date): row.count for row in created_result.all()}

    # Get completed counts by date
    completed_result = await db.execute(
        select(
            func.date(Meeting.updated_at).label("date"),
            func.count(Meeting.id).label("count"),
        )
        .where(
            and_(
                Meeting.user_id == current_user.id,
                Meeting.status == MeetingStatus.COMPLETED,
                func.date(Meeting.updated_at) >= start_date,
            )
        )
        .group_by(func.date(Meeting.updated_at))
    )
    completed_by_date = {str(row.date): row.count for row in completed_result.all()}

    # Get failed counts by date
    failed_result = await db.execute(
        select(
            func.date(Meeting.updated_at).label("date"),
            func.count(Meeting.id).label("count"),
        )
        .where(
            and_(
                Meeting.user_id == current_user.id,
                Meeting.status == MeetingStatus.FAILED,
                func.date(Meeting.updated_at) >= start_date,
            )
        )
        .group_by(func.date(Meeting.updated_at))
    )
    failed_by_date = {str(row.date): row.count for row in failed_result.all()}

    # Build response
    stats = []
    current_date = start_date
    while current_date <= end_date:
        date_str = str(current_date)
        stats.append(DailyStats(
            date=date_str,
            meetings_created=created_by_date.get(date_str, 0),
            meetings_completed=completed_by_date.get(date_str, 0),
            meetings_failed=failed_by_date.get(date_str, 0),
        ))
        current_date += timedelta(days=1)

    return stats


@router.get("/user", response_model=UserMetrics)
async def get_user_metrics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get user-specific metrics

    Returns statistics for the current user.
    """
    # Count meetings
    meeting_result = await db.execute(
        select(
            func.count(Meeting.id).label("total"),
            func.sum(
                func.case(
                    (Meeting.status == MeetingStatus.COMPLETED, 1),
                    else_=0
                )
            ).label("completed"),
            func.sum(
                func.case(
                    (Meeting.status == MeetingStatus.REVIEW_PENDING, 1),
                    else_=0
                )
            ).label("pending_review"),
        )
        .where(Meeting.user_id == current_user.id)
    )

    row = meeting_result.one()

    # TODO: Add action item counts when ActionItem model is connected

    return UserMetrics(
        total_meetings=row.total or 0,
        completed_meetings=row.completed or 0,
        pending_review=row.pending_review or 0,
        total_action_items=0,  # Placeholder
        completed_action_items=0,  # Placeholder
    )


@router.get("/pipeline/status")
async def get_pipeline_status(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get current pipeline processing status

    Returns information about currently processing meetings.
    """
    # Get processing meetings
    result = await db.execute(
        select(Meeting)
        .where(
            and_(
                Meeting.user_id == current_user.id,
                Meeting.status == MeetingStatus.PROCESSING,
            )
        )
        .order_by(Meeting.created_at.desc())
        .limit(10)
    )

    processing_meetings = result.scalars().all()

    return {
        "active_count": len(processing_meetings),
        "meetings": [
            {
                "id": str(m.id),
                "title": m.title,
                "started_at": m.created_at.isoformat(),
                "duration_seconds": (datetime.utcnow() - m.created_at).total_seconds(),
            }
            for m in processing_meetings
        ],
    }
