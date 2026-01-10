"""
LangGraph State Schema for Meeting Processing Pipeline
"""

from typing import TypedDict, List, Optional, Literal, Annotated
from datetime import datetime
import operator


class TranscriptSegment(TypedDict):
    """Single transcript segment from STT"""
    speaker: str
    text: str
    start_time: float
    end_time: float
    confidence: Optional[float]


class ActionItem(TypedDict):
    """Extracted action item"""
    content: str
    assignee: Optional[str]
    due_date: Optional[str]  # ISO format YYYY-MM-DD
    priority: Literal["low", "medium", "high", "urgent"]


class MeetingAgentState(TypedDict):
    """
    State schema for the Meeting Processing Agent
    
    This state flows through all nodes in the LangGraph pipeline:
    STT → Summarizer → ActionExtractor → Critique → HumanReview → Save
    """
    
    # === Input ===
    meeting_id: str
    audio_file_url: str
    meeting_title: str
    meeting_date: Optional[str]
    
    # === STT Output ===
    transcript_segments: Annotated[List[TranscriptSegment], operator.add]
    raw_text: str
    speakers: List[str]
    audio_duration: float
    
    # === LLM Outputs ===
    draft_summary: str
    key_points: List[str]
    decisions: List[str]
    action_items: List[ActionItem]
    
    # === Quality Control ===
    critique: str
    critique_issues: List[str]
    critique_passed: bool
    retry_count: int
    
    # === Human-in-the-Loop ===
    requires_human_review: bool
    human_feedback: Optional[str]
    human_approved: bool
    
    # === Final Output ===
    final_summary: Optional[str]
    final_key_points: Optional[List[str]]
    final_decisions: Optional[List[str]]
    final_action_items: Optional[List[ActionItem]]
    
    # === Metadata ===
    status: Literal[
        "started",
        "stt_complete",
        "summarized",
        "actions_extracted",
        "critique_complete",
        "pending_review",
        "completed",
        "failed"
    ]
    error_message: Optional[str]
    started_at: str
    completed_at: Optional[str]


def create_initial_state(
    meeting_id: str,
    audio_file_url: str,
    meeting_title: str,
    meeting_date: Optional[str] = None
) -> MeetingAgentState:
    """
    Create initial state for a new meeting processing job
    
    Args:
        meeting_id: UUID of the meeting
        audio_file_url: URL to the audio file in storage
        meeting_title: Title of the meeting
        meeting_date: Optional date of the meeting (YYYY-MM-DD)
    
    Returns:
        Initial MeetingAgentState
    """
    return MeetingAgentState(
        # Input
        meeting_id=meeting_id,
        audio_file_url=audio_file_url,
        meeting_title=meeting_title,
        meeting_date=meeting_date,
        
        # STT Output (empty initially)
        transcript_segments=[],
        raw_text="",
        speakers=[],
        audio_duration=0.0,
        
        # LLM Outputs (empty initially)
        draft_summary="",
        key_points=[],
        decisions=[],
        action_items=[],
        
        # Quality Control
        critique="",
        critique_issues=[],
        critique_passed=False,
        retry_count=0,
        
        # Human-in-the-Loop
        requires_human_review=True,  # Default to requiring review
        human_feedback=None,
        human_approved=False,
        
        # Final Output
        final_summary=None,
        final_key_points=None,
        final_decisions=None,
        final_action_items=None,
        
        # Metadata
        status="started",
        error_message=None,
        started_at=datetime.utcnow().isoformat(),
        completed_at=None,
    )
