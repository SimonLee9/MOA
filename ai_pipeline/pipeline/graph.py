"""
LangGraph Meeting Processing Pipeline
Main graph definition and execution
"""

from typing import Literal
from datetime import datetime

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from pipeline.state import MeetingAgentState, create_initial_state


# === Node Functions ===

async def stt_node(state: MeetingAgentState) -> dict:
    """
    Speech-to-Text Node
    Converts audio to text with speaker diarization
    """
    from pipeline.integrations.clova_stt import transcribe_audio, get_clova_client
    
    try:
        # Transcribe audio
        result = await transcribe_audio(state["audio_file_url"])
        
        # Format transcript for LLM
        client = get_clova_client()
        formatted_transcript = client.format_transcript(result)
        
        # Convert segments to dict format
        segments = [
            {
                "speaker": seg.speaker,
                "text": seg.text,
                "start_time": seg.start_time,
                "end_time": seg.end_time,
                "confidence": seg.confidence,
            }
            for seg in result.segments
        ]
        
        return {
            "transcript_segments": segments,
            "raw_text": formatted_transcript,
            "speakers": result.speakers,
            "audio_duration": result.duration,
            "status": "stt_complete",
        }
    
    except Exception as e:
        return {
            "status": "failed",
            "error_message": f"STT failed: {str(e)}",
        }


async def summarizer_node(state: MeetingAgentState) -> dict:
    """
    Summarizer Node
    Generates meeting summary using Claude
    """
    from pipeline.integrations.claude_llm import generate_summary
    
    try:
        result = await generate_summary(
            transcript=state["raw_text"],
            meeting_title=state["meeting_title"],
            meeting_date=state["meeting_date"],
            speakers=state["speakers"],
        )
        
        return {
            "draft_summary": result.get("summary", ""),
            "key_points": result.get("key_points", []),
            "decisions": result.get("decisions", []),
            "status": "summarized",
        }
    
    except Exception as e:
        return {
            "status": "failed",
            "error_message": f"Summarization failed: {str(e)}",
        }


async def action_extractor_node(state: MeetingAgentState) -> dict:
    """
    Action Extractor Node
    Extracts action items from the meeting
    """
    from pipeline.integrations.claude_llm import extract_actions
    
    try:
        result = await extract_actions(
            transcript=state["raw_text"],
            summary=state["draft_summary"],
            meeting_title=state["meeting_title"],
            meeting_date=state["meeting_date"],
            speakers=state["speakers"],
        )
        
        return {
            "action_items": result.get("action_items", []),
            "status": "actions_extracted",
        }
    
    except Exception as e:
        return {
            "status": "failed",
            "error_message": f"Action extraction failed: {str(e)}",
        }


async def critique_node(state: MeetingAgentState) -> dict:
    """
    Critique Node
    Validates the quality of generated content
    """
    from pipeline.integrations.claude_llm import critique_results
    
    try:
        result = await critique_results(
            transcript=state["raw_text"],
            summary=state["draft_summary"],
            key_points=state["key_points"],
            decisions=state["decisions"],
            action_items=state["action_items"],
        )
        
        return {
            "critique": result.get("critique", ""),
            "critique_issues": result.get("issues", []),
            "critique_passed": result.get("passed", False),
            "retry_count": state["retry_count"] + 1 if not result.get("passed", False) else state["retry_count"],
            "status": "critique_complete",
        }
    
    except Exception as e:
        # If critique fails, assume it passed to avoid blocking
        return {
            "critique": f"Critique failed: {str(e)}",
            "critique_issues": [],
            "critique_passed": True,
            "status": "critique_complete",
        }


async def human_review_node(state: MeetingAgentState) -> dict:
    """
    Human Review Node
    Uses interrupt() to pause execution and wait for human approval

    This implements the Human-in-the-Loop (HITL) pattern from the guide.
    The graph execution will pause here until the user approves/rejects via API.
    """
    from langgraph.types import interrupt

    # Prepare review data for the user
    review_data = {
        "type": "review_request",
        "meeting_id": state["meeting_id"],
        "minutes": state["draft_summary"],
        "key_points": state["key_points"],
        "decisions": state["decisions"],
        "proposed_actions": state["action_items"],
        "critique": state.get("critique", ""),
    }

    # This will pause execution and wait for human input
    # User must call the resume API with their decision
    user_decision = interrupt(review_data)

    # After resume, process user's decision
    if user_decision and user_decision.get("action") == "approve":
        # User approved, possibly with modifications
        updated_actions = user_decision.get("updated_actions", state["action_items"])
        updated_summary = user_decision.get("updated_summary", state["draft_summary"])
        updated_key_points = user_decision.get("updated_key_points", state["key_points"])
        updated_decisions = user_decision.get("updated_decisions", state["decisions"])

        return {
            "final_summary": updated_summary,
            "final_key_points": updated_key_points,
            "final_decisions": updated_decisions,
            "final_action_items": updated_actions,
            "human_approved": True,
            "human_feedback": user_decision.get("feedback", "Approved"),
            "status": "approved",
        }
    else:
        # User rejected, return to summarizer with feedback
        return {
            "human_approved": False,
            "human_feedback": user_decision.get("feedback", "Rejected - needs revision"),
            "status": "revision_requested",
            "retry_count": state.get("retry_count", 0) + 1,
        }


async def save_node(state: MeetingAgentState) -> dict:
    """
    Save Node
    Saves the final results to database
    """
    # In a real implementation, this would save to the database
    # For now, just mark as completed
    return {
        "status": "completed",
        "human_approved": True,
        "completed_at": datetime.utcnow().isoformat(),
    }


# === Routing Functions ===

def route_after_critique(state: MeetingAgentState) -> Literal["human_review", "summarizer", "end"]:
    """
    Route after critique based on results

    Flow:
    - If critique passed: go to human review
    - If critique failed and retry_count < 3: retry summarization with feedback
    - If critique failed and retry_count >= 3: proceed to human review anyway
    - If system error: end workflow
    """
    # Check for fatal errors
    if state.get("status") == "failed":
        return "end"

    # If critique passed, proceed to human review
    if state.get("critique_passed", False):
        return "human_review"

    # If critique failed, check retry count
    retry_count = state.get("retry_count", 0)

    if retry_count < 3:
        # Retry with critique feedback
        return "summarizer"
    else:
        # Max retries reached, let human decide
        return "human_review"


def route_after_human_review(state: MeetingAgentState) -> Literal["save", "summarizer", "end"]:
    """
    Route after human review based on approval

    Flow:
    - If approved: save results
    - If rejected and can retry: go back to summarizer with human feedback
    - If rejected and max retries: end with failure
    """
    # If approved, save and complete
    if state.get("human_approved", False):
        return "save"

    # If rejected, check if we can retry
    retry_count = state.get("retry_count", 0)

    if retry_count < 5:  # Allow more retries for human feedback
        return "summarizer"
    else:
        # Max retries reached, end workflow
        return "end"


def route_after_stt(state: MeetingAgentState) -> Literal["summarizer", "end"]:
    """Route after STT - continue or fail"""
    if state.get("status") == "failed":
        return "end"
    return "summarizer"


# === Graph Builder ===

async def create_meeting_graph():
    """
    Create the meeting processing LangGraph with PostgreSQL persistence

    Enhanced Flow (following the guide):
    STT -> Summarizer -> ActionExtractor -> Critique -> HumanReview -> Save
              ^              ^                  |             |
              |_____________(auto retry)________|             |
              |_____________(human feedback)_________________|

    Key Features:
    1. PostgreSQL checkpointer for long-running workflows
    2. Human-in-the-loop with interrupt() pattern
    3. Automatic retry loop based on critique
    4. Human feedback loop for revision requests

    Returns:
        Compiled LangGraph with PostgreSQL checkpointing
    """
    from pipeline.checkpointer import get_checkpointer

    builder = StateGraph(MeetingAgentState)

    # Add nodes
    builder.add_node("stt", stt_node)
    builder.add_node("summarizer", summarizer_node)
    builder.add_node("extract_actions", action_extractor_node)
    builder.add_node("critique", critique_node)
    builder.add_node("human_review", human_review_node)
    builder.add_node("save", save_node)

    # Set entry point
    builder.set_entry_point("stt")

    # Add edges
    builder.add_conditional_edges(
        "stt",
        route_after_stt,
        {
            "summarizer": "summarizer",
            "end": END,
        }
    )

    builder.add_edge("summarizer", "extract_actions")
    builder.add_edge("extract_actions", "critique")

    # Conditional edge after critique (automatic retry loop)
    builder.add_conditional_edges(
        "critique",
        route_after_critique,
        {
            "human_review": "human_review",
            "summarizer": "summarizer",
            "end": END,
        }
    )

    # Conditional edge after human review (human feedback loop)
    builder.add_conditional_edges(
        "human_review",
        route_after_human_review,
        {
            "save": "save",
            "summarizer": "summarizer",
            "end": END,
        }
    )

    builder.add_edge("save", END)

    # Get PostgreSQL checkpointer for persistent state
    checkpointer = await get_checkpointer()

    # Compile with PostgreSQL checkpointing
    # Note: interrupt_before is removed since we use interrupt() inside the node
    graph = builder.compile(
        checkpointer=checkpointer,
    )

    return graph


# === Execution Functions ===

async def process_meeting(
    meeting_id: str,
    audio_file_url: str,
    meeting_title: str,
    meeting_date: str = None,
) -> MeetingAgentState:
    """
    Process a meeting through the full pipeline

    This function initiates the LangGraph workflow which will:
    1. Transcribe audio (STT)
    2. Generate summary and extract action items
    3. Self-critique the results
    4. Pause for human review (via interrupt)
    5. Save approved results

    Args:
        meeting_id: UUID of the meeting (used as thread_id)
        audio_file_url: URL/path to the audio file
        meeting_title: Title of the meeting
        meeting_date: Optional date string (YYYY-MM-DD)

    Returns:
        Final state after processing
        Note: Will be interrupted at human_review_node
    """
    graph = await create_meeting_graph()

    # Create initial state
    initial_state = create_initial_state(
        meeting_id=meeting_id,
        audio_file_url=audio_file_url,
        meeting_title=meeting_title,
        meeting_date=meeting_date,
    )

    # Configure with thread_id for checkpoint persistence
    config = {"configurable": {"thread_id": meeting_id}}

    # Run the graph (will pause at interrupt)
    final_state = await graph.ainvoke(initial_state, config)

    return final_state


async def resume_after_review(
    meeting_id: str,
    action: str = "approve",
    feedback: str = None,
    updated_summary: str = None,
    updated_key_points: list = None,
    updated_decisions: list = None,
    updated_actions: list = None,
) -> MeetingAgentState:
    """
    Resume processing after human review

    This function is called when a user approves or rejects the meeting results.
    It uses the Command API to pass data to the interrupted node.

    Args:
        meeting_id: UUID of the meeting (thread_id)
        action: "approve" or "reject"
        feedback: Optional human feedback text
        updated_summary: Optional modified summary
        updated_key_points: Optional modified key points
        updated_decisions: Optional modified decisions
        updated_actions: Optional modified action items

    Returns:
        Final state after completion or revision
    """
    from langgraph.types import Command

    graph = await create_meeting_graph()
    config = {"configurable": {"thread_id": meeting_id}}

    # Prepare user decision data for the interrupt() call
    user_decision = {
        "action": action,
        "feedback": feedback,
        "updated_summary": updated_summary,
        "updated_key_points": updated_key_points,
        "updated_decisions": updated_decisions,
        "updated_actions": updated_actions,
    }

    # Resume with Command to pass data to interrupt()
    final_state = await graph.ainvoke(
        Command(resume=user_decision),
        config
    )

    return final_state
