"""
Tus Protocol Upload API
Handles resumable audio file uploads
"""

import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi_tusd import TusRouter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import get_current_user
from app.config import settings
from app.models.user import User
from app.models.meeting import Meeting, MeetingStatus


router = APIRouter(prefix="/upload", tags=["Tus Upload"])

# Upload directory
UPLOAD_DIR = Path(settings.upload_dir if hasattr(settings, 'upload_dir') else "./meeting_uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# === Tus Upload Hooks ===

async def on_upload_complete(file_id: str, file_path: str):
    """
    Called when a Tus upload completes
    This is where we'll trigger the LangGraph processing
    """
    print(f"Upload complete: {file_id} -> {file_path}")
    # TODO: Trigger LangGraph workflow
    # This will be implemented when we integrate with the AI pipeline


# === Tus Router Configuration ===

try:
    # Try new API first (fastapi-tusd >= 0.100)
    tus_config = {
        "store_dir": str(UPLOAD_DIR),
        "location": "/api/v1/upload/files",
        "max_size": 2 * 1024 * 1024 * 1024,  # 2GB max file size
    }
    tus_router = TusRouter(**tus_config)
except TypeError:
    # Fallback for older versions with upload_finish_cb
    tus_config = {
        "store_dir": str(UPLOAD_DIR),
        "location": "/api/v1/upload/files",
        "max_size": 2 * 1024 * 1024 * 1024,
        "upload_finish_cb": on_upload_complete,
    }
    tus_router = TusRouter(**tus_config)

router.include_router(tus_router, prefix="/files")


# === Meeting Processing Endpoints ===

@router.post("/meetings/{meeting_id}/process")
async def start_meeting_processing(
    meeting_id: str,
    file_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Start AI processing for a meeting after Tus upload completes

    Args:
        meeting_id: UUID of the meeting
        file_id: Tus upload file ID
        background_tasks: FastAPI background tasks

    Flow:
        1. Verify meeting exists and belongs to user
        2. Verify uploaded file exists
        3. Update meeting with file path
        4. Trigger LangGraph workflow in background
    """
    # Verify meeting exists and belongs to user
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == uuid.UUID(meeting_id),
            Meeting.user_id == current_user.id
        )
    )
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )

    # Verify file exists
    file_path = UPLOAD_DIR / file_id
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Uploaded file not found. Please ensure upload completed successfully."
        )

    # Get file info
    file_size = file_path.stat().st_size

    # Update meeting status
    meeting.audio_file_url = f"file://{file_path.absolute()}"
    meeting.status = MeetingStatus.PROCESSING
    await db.commit()

    # Start LangGraph processing in background
    background_tasks.add_task(
        trigger_langgraph_workflow,
        meeting_id=meeting_id,
        audio_file_path=str(file_path.absolute()),
        meeting_title=meeting.title,
        meeting_date=str(meeting.meeting_date) if meeting.meeting_date else None,
    )

    return {
        "meeting_id": meeting_id,
        "status": "processing_started",
        "file_size": file_size,
        "message": "AI processing has been started. Check the meeting status endpoint for progress.",
    }


async def trigger_langgraph_workflow(
    meeting_id: str,
    audio_file_path: str,
    meeting_title: str,
    meeting_date: Optional[str] = None,
):
    """
    Trigger the LangGraph workflow for meeting processing

    This runs in the background and processes the meeting through:
    1. STT (Speech-to-Text)
    2. Summarization
    3. Action item extraction
    4. Quality critique
    5. Human review (interrupted)
    """
    try:
        # Import here to avoid circular dependencies
        from ai_pipeline.pipeline.graph import process_meeting

        # Run the graph
        result = await process_meeting(
            meeting_id=meeting_id,
            audio_file_url=audio_file_path,
            meeting_title=meeting_title,
            meeting_date=meeting_date,
        )

        print(f"Meeting {meeting_id} processed: {result.get('status')}")

    except Exception as e:
        print(f"Error processing meeting {meeting_id}: {str(e)}")
        # TODO: Update meeting status to FAILED in database
        raise


@router.get("/meetings/{meeting_id}/status")
async def get_processing_status(
    meeting_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the current processing status of a meeting

    This endpoint retrieves the state from LangGraph's checkpoint
    to show progress through the workflow
    """
    # Verify meeting exists and belongs to user
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == uuid.UUID(meeting_id),
            Meeting.user_id == current_user.id
        )
    )
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )

    # Get state from LangGraph
    try:
        from ai_pipeline.pipeline.graph import create_meeting_graph

        graph = create_meeting_graph()
        config = {"configurable": {"thread_id": meeting_id}}

        # Get current state
        state_snapshot = await graph.aget_state(config)

        if state_snapshot and state_snapshot.values:
            current_state = state_snapshot.values

            return {
                "meeting_id": meeting_id,
                "status": current_state.get("status", "unknown"),
                "requires_review": current_state.get("requires_human_review", False),
                "progress": {
                    "stt_complete": bool(current_state.get("raw_text")),
                    "summary_complete": bool(current_state.get("draft_summary")),
                    "actions_extracted": bool(current_state.get("action_items")),
                    "critique_complete": bool(current_state.get("critique")),
                },
                "error": current_state.get("error_message"),
            }
        else:
            # No state yet, check database
            return {
                "meeting_id": meeting_id,
                "status": meeting.status.value,
                "requires_review": False,
                "progress": {},
            }

    except Exception as e:
        # Fallback to database status
        return {
            "meeting_id": meeting_id,
            "status": meeting.status.value,
            "error": f"Failed to get detailed status: {str(e)}",
        }
