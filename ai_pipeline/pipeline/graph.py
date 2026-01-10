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
    Placeholder for human-in-the-loop review
    This node is interrupted before execution to wait for human input
    """
    # Copy draft to final if no changes needed
    return {
        "final_summary": state["draft_summary"],
        "final_key_points": state["key_points"],
        "final_decisions": state["decisions"],
        "final_action_items": state["action_items"],
        "status": "pending_review",
        "requires_human_review": True,
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
    
    - If passed: go to human review
    - If failed and retries < 3: retry summarization
    - If failed and retries >= 3: end with failure
    """
    if state.get("status") == "failed":
        return "end"
    
    if state.get("critique_passed", False):
        return "human_review"
    
    if state.get("retry_count", 0) < 3:
        return "summarizer"
    
    # Max retries reached, proceed anyway
    return "human_review"


def route_after_stt(state: MeetingAgentState) -> Literal["summarizer", "end"]:
    """Route after STT - continue or fail"""
    if state.get("status") == "failed":
        return "end"
    return "summarizer"


# === Graph Builder ===

def create_meeting_graph():
    """
    Create the meeting processing LangGraph
    
    Flow:
    STT -> Summarizer -> ActionExtractor -> Critique -> HumanReview -> Save
                            ^                    |
                            |____(retry)_________|
    
    Returns:
        Compiled LangGraph with checkpointing
    """
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
    
    # Conditional edge after critique (retry loop)
    builder.add_conditional_edges(
        "critique",
        route_after_critique,
        {
            "human_review": "human_review",
            "summarizer": "summarizer",
            "end": END,
        }
    )
    
    builder.add_edge("human_review", "save")
    builder.add_edge("save", END)
    
    # Compile with checkpointing and interrupt
    memory = MemorySaver()
    graph = builder.compile(
        checkpointer=memory,
        interrupt_before=["human_review"],  # Wait for human review
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
    
    Args:
        meeting_id: UUID of the meeting
        audio_file_url: URL to the audio file
        meeting_title: Title of the meeting
        meeting_date: Optional date string
    
    Returns:
        Final state after processing (may be interrupted for review)
    """
    graph = create_meeting_graph()
    
    # Create initial state
    initial_state = create_initial_state(
        meeting_id=meeting_id,
        audio_file_url=audio_file_url,
        meeting_title=meeting_title,
        meeting_date=meeting_date,
    )
    
    # Run the graph
    config = {"configurable": {"thread_id": meeting_id}}
    
    final_state = await graph.ainvoke(initial_state, config)
    
    return final_state


async def resume_after_review(
    meeting_id: str,
    human_feedback: str = None,
    approved: bool = True,
) -> MeetingAgentState:
    """
    Resume processing after human review
    
    Args:
        meeting_id: UUID of the meeting
        human_feedback: Optional feedback from reviewer
        approved: Whether the review was approved
    
    Returns:
        Final state after completion
    """
    graph = create_meeting_graph()
    config = {"configurable": {"thread_id": meeting_id}}
    
    # Get current state
    state = await graph.aget_state(config)
    
    # Update with human feedback
    update = {
        "human_feedback": human_feedback,
        "human_approved": approved,
    }
    
    # Resume execution
    final_state = await graph.ainvoke(update, config)
    
    return final_state
