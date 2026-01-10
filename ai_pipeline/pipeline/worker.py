"""
Celery Worker for AI Pipeline
Handles async meeting processing tasks
"""

import asyncio
from celery import Celery
from pydantic_settings import BaseSettings


class WorkerSettings(BaseSettings):
    """Worker settings"""
    redis_url: str = "redis://localhost:6379"
    database_url: str = ""
    
    class Config:
        env_file = ".env"


settings = WorkerSettings()

# Create Celery app
app = Celery(
    "moa_worker",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

# Celery configuration
app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    worker_prefetch_multiplier=1,  # Process one task at a time
)


def run_async(coro):
    """Helper to run async functions in Celery"""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coro)


@app.task(bind=True, max_retries=3)
def process_meeting_task(
    self,
    meeting_id: str,
    audio_file_url: str,
    meeting_title: str,
    meeting_date: str = None,
):
    """
    Celery task to process a meeting
    
    Args:
        meeting_id: UUID of the meeting
        audio_file_url: URL to the audio file
        meeting_title: Title of the meeting
        meeting_date: Optional date string
    """
    from pipeline.graph import process_meeting
    
    try:
        # Run the async pipeline
        result = run_async(
            process_meeting(
                meeting_id=meeting_id,
                audio_file_url=audio_file_url,
                meeting_title=meeting_title,
                meeting_date=meeting_date,
            )
        )
        
        # Update database with results
        # This would be implemented to save results to PostgreSQL
        _save_results_to_db(meeting_id, result)
        
        return {
            "meeting_id": meeting_id,
            "status": result.get("status", "unknown"),
            "error": result.get("error_message"),
        }
    
    except Exception as e:
        # Retry on failure
        self.retry(exc=e, countdown=60)  # Retry after 60 seconds


@app.task
def resume_meeting_task(
    meeting_id: str,
    human_feedback: str = None,
    approved: bool = True,
):
    """
    Celery task to resume meeting processing after human review
    
    Args:
        meeting_id: UUID of the meeting
        human_feedback: Optional feedback from reviewer
        approved: Whether the review was approved
    """
    from pipeline.graph import resume_after_review
    
    result = run_async(
        resume_after_review(
            meeting_id=meeting_id,
            human_feedback=human_feedback,
            approved=approved,
        )
    )
    
    # Save final results
    _save_results_to_db(meeting_id, result)
    
    return {
        "meeting_id": meeting_id,
        "status": result.get("status", "unknown"),
    }


def _save_results_to_db(meeting_id: str, state: dict):
    """
    Save processing results to database
    
    This is a placeholder - in production, this would:
    1. Connect to PostgreSQL
    2. Update the meeting status
    3. Save summary, transcripts, action items
    """
    import json
    
    # For now, just log the results
    print(f"Saving results for meeting {meeting_id}:")
    print(f"  Status: {state.get('status')}")
    print(f"  Summary length: {len(state.get('draft_summary', ''))}")
    print(f"  Action items: {len(state.get('action_items', []))}")
    
    # TODO: Implement actual database save
    # This would use SQLAlchemy to update:
    # - meetings table (status)
    # - meeting_summaries table
    # - transcripts table
    # - action_items table
