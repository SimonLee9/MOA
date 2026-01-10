"""
Human Review API
Handles human-in-the-loop review and approval
"""

from uuid import UUID
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.meeting import Meeting


router = APIRouter(prefix="/meetings", tags=["Review"])


# === Request/Response Models ===


class ActionItemUpdate(BaseModel):
    """Updated action item from user"""
    id: str
    content: str
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    priority: str = "medium"
    status: str = "approved"


class ReviewDecision(BaseModel):
    """User's review decision"""
    action: str = Field(..., description="'approve' or 'reject'")
    feedback: Optional[str] = Field(None, description="Optional feedback for revision")

    # Optional modifications
    updated_summary: Optional[str] = None
    updated_key_points: Optional[List[str]] = None
    updated_decisions: Optional[List[str]] = None
    updated_actions: Optional[List[ActionItemUpdate]] = None


class ReviewStatusResponse(BaseModel):
    """Current review status"""
    meeting_id: str
    status: str
    requires_review: bool
    review_data: Optional[dict] = None


# === Endpoints ===


@router.get("/{meeting_id}/review", response_model=ReviewStatusResponse)
async def get_review_status(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get the current review status for a meeting

    This retrieves the interrupted state from LangGraph to show
    what needs to be reviewed.

    Returns:
        Review data if waiting for review, otherwise status info
    """
    # Verify meeting belongs to user
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

    # Get state from LangGraph
    try:
        from ai_pipeline.pipeline.graph import create_meeting_graph

        graph = await create_meeting_graph()
        config = {"configurable": {"thread_id": str(meeting_id)}}

        # Get current state
        state_snapshot = await graph.aget_state(config)

        if not state_snapshot or not state_snapshot.values:
            return ReviewStatusResponse(
                meeting_id=str(meeting_id),
                status=meeting.status.value,
                requires_review=False,
                review_data=None,
            )

        current_state = state_snapshot.values

        # Check if waiting for review (interrupted)
        requires_review = current_state.get("requires_human_review", False)

        if requires_review:
            # Extract review data
            review_data = {
                "minutes": current_state.get("draft_summary", ""),
                "key_points": current_state.get("key_points", []),
                "decisions": current_state.get("decisions", []),
                "proposed_actions": current_state.get("action_items", []),
                "critique": current_state.get("critique", ""),
                "retry_count": current_state.get("retry_count", 0),
            }
        else:
            review_data = None

        return ReviewStatusResponse(
            meeting_id=str(meeting_id),
            status=current_state.get("status", "unknown"),
            requires_review=requires_review,
            review_data=review_data,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get review status: {str(e)}"
        )


@router.post("/{meeting_id}/review", response_model=dict)
async def submit_review(
    meeting_id: UUID,
    decision: ReviewDecision,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Submit a review decision (approve or reject)

    This resumes the LangGraph workflow with the user's decision.

    Flow:
    - If approved: Workflow continues to save results
    - If rejected: Workflow goes back to summarizer with feedback

    Args:
        meeting_id: Meeting UUID
        decision: User's review decision and optional modifications

    Returns:
        Updated workflow status
    """
    # Verify meeting belongs to user
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

    # Resume LangGraph workflow
    try:
        from ai_pipeline.pipeline.graph import resume_after_review

        # Convert ActionItemUpdate to dict
        updated_actions = None
        if decision.updated_actions:
            updated_actions = [action.model_dump() for action in decision.updated_actions]

        # Resume with decision
        final_state = await resume_after_review(
            meeting_id=str(meeting_id),
            action=decision.action,
            feedback=decision.feedback,
            updated_summary=decision.updated_summary,
            updated_key_points=decision.updated_key_points,
            updated_decisions=decision.updated_decisions,
            updated_actions=updated_actions,
        )

        # Return status
        return {
            "meeting_id": str(meeting_id),
            "status": final_state.get("status", "processing"),
            "action": decision.action,
            "message": f"Review {decision.action}d successfully. Workflow resumed.",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit review: {str(e)}"
        )


@router.get("/{meeting_id}/results", response_model=dict)
async def get_meeting_results(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get final meeting results after approval

    Returns the completed meeting summary, action items, and execution results.

    Args:
        meeting_id: Meeting UUID

    Returns:
        Final meeting results
    """
    # Verify meeting belongs to user
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

    # Get final state from LangGraph
    try:
        from ai_pipeline.pipeline.graph import create_meeting_graph

        graph = await create_meeting_graph()
        config = {"configurable": {"thread_id": str(meeting_id)}}

        state_snapshot = await graph.aget_state(config)

        if not state_snapshot or not state_snapshot.values:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No results found. Meeting may not have been processed yet."
            )

        state = state_snapshot.values

        # Check if completed
        if state.get("status") != "completed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Meeting not completed yet. Current status: {state.get('status')}"
            )

        return {
            "meeting_id": str(meeting_id),
            "status": "completed",
            "summary": state.get("final_summary", ""),
            "key_points": state.get("final_key_points", []),
            "decisions": state.get("final_decisions", []),
            "action_items": state.get("final_action_items", []),
            "execution_results": state.get("execution_results", []),
            "human_approved": state.get("human_approved", False),
            "completed_at": state.get("completed_at"),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get results: {str(e)}"
        )
