"""
Tests for Meeting Agent State
"""

import pytest
from datetime import datetime

from pipeline.state import (
    MeetingAgentState,
    TranscriptSegment,
    ActionItem,
    create_initial_state,
)


class TestCreateInitialState:
    """Tests for create_initial_state function."""

    def test_creates_valid_state(self, sample_meeting_id, sample_audio_url):
        """Test basic state creation."""
        state = create_initial_state(
            meeting_id=sample_meeting_id,
            audio_file_url=sample_audio_url,
            meeting_title="Test Meeting",
        )

        assert state["meeting_id"] == sample_meeting_id
        assert state["audio_file_url"] == sample_audio_url
        assert state["meeting_title"] == "Test Meeting"
        assert state["status"] == "started"

    def test_includes_optional_date(self, sample_meeting_id, sample_audio_url):
        """Test state with meeting date."""
        state = create_initial_state(
            meeting_id=sample_meeting_id,
            audio_file_url=sample_audio_url,
            meeting_title="Test Meeting",
            meeting_date="2024-01-15",
        )

        assert state["meeting_date"] == "2024-01-15"

    def test_initializes_empty_collections(self, sample_meeting_id, sample_audio_url):
        """Test empty collections are initialized."""
        state = create_initial_state(
            meeting_id=sample_meeting_id,
            audio_file_url=sample_audio_url,
            meeting_title="Test Meeting",
        )

        assert state["transcript_segments"] == []
        assert state["speakers"] == []
        assert state["key_points"] == []
        assert state["decisions"] == []
        assert state["action_items"] == []
        assert state["critique_issues"] == []

    def test_initializes_default_values(self, sample_meeting_id, sample_audio_url):
        """Test default values are set correctly."""
        state = create_initial_state(
            meeting_id=sample_meeting_id,
            audio_file_url=sample_audio_url,
            meeting_title="Test Meeting",
        )

        assert state["raw_text"] == ""
        assert state["draft_summary"] == ""
        assert state["audio_duration"] == 0.0
        assert state["retry_count"] == 0
        assert state["critique_passed"] is False
        assert state["requires_human_review"] is True
        assert state["human_approved"] is False

    def test_sets_started_at_timestamp(self, sample_meeting_id, sample_audio_url):
        """Test started_at is set to current time."""
        before = datetime.utcnow().isoformat()

        state = create_initial_state(
            meeting_id=sample_meeting_id,
            audio_file_url=sample_audio_url,
            meeting_title="Test Meeting",
        )

        after = datetime.utcnow().isoformat()

        assert state["started_at"] >= before
        assert state["started_at"] <= after
        assert state["completed_at"] is None

    def test_final_outputs_are_none(self, sample_meeting_id, sample_audio_url):
        """Test final outputs start as None."""
        state = create_initial_state(
            meeting_id=sample_meeting_id,
            audio_file_url=sample_audio_url,
            meeting_title="Test Meeting",
        )

        assert state["final_summary"] is None
        assert state["final_key_points"] is None
        assert state["final_decisions"] is None
        assert state["final_action_items"] is None


class TestTranscriptSegment:
    """Tests for TranscriptSegment type."""

    def test_valid_segment(self):
        """Test valid transcript segment."""
        segment: TranscriptSegment = {
            "speaker": "홍길동",
            "text": "안녕하세요.",
            "start_time": 0.0,
            "end_time": 1.5,
            "confidence": 0.95,
        }

        assert segment["speaker"] == "홍길동"
        assert segment["text"] == "안녕하세요."
        assert segment["start_time"] == 0.0
        assert segment["end_time"] == 1.5
        assert segment["confidence"] == 0.95

    def test_segment_without_confidence(self):
        """Test segment with optional confidence."""
        segment: TranscriptSegment = {
            "speaker": "홍길동",
            "text": "안녕하세요.",
            "start_time": 0.0,
            "end_time": 1.5,
            "confidence": None,
        }

        assert segment["confidence"] is None


class TestActionItem:
    """Tests for ActionItem type."""

    def test_valid_action_item(self):
        """Test valid action item."""
        action: ActionItem = {
            "id": "action-1",
            "content": "보고서 작성",
            "assignee": "홍길동",
            "due_date": "2024-01-20",
            "priority": "high",
            "tool_call_payload": None,
            "status": "pending",
        }

        assert action["id"] == "action-1"
        assert action["content"] == "보고서 작성"
        assert action["priority"] == "high"
        assert action["status"] == "pending"

    def test_action_item_with_tool_payload(self):
        """Test action item with MCP tool payload."""
        action: ActionItem = {
            "id": "action-2",
            "content": "Jira 티켓 생성",
            "assignee": None,
            "due_date": None,
            "priority": "medium",
            "tool_call_payload": {
                "tool": "jira_create_issue",
                "args": {"project": "PROJ", "summary": "New task"},
            },
            "status": "pending",
        }

        assert action["tool_call_payload"]["tool"] == "jira_create_issue"
        assert action["tool_call_payload"]["args"]["project"] == "PROJ"


class TestStateTransitions:
    """Tests for state transitions."""

    def test_initial_to_stt_complete(self, initial_state, sample_transcript_segments):
        """Test transition from initial to STT complete."""
        state = initial_state.copy()
        state.update({
            "transcript_segments": sample_transcript_segments,
            "raw_text": "Test transcript",
            "speakers": ["Speaker 1", "Speaker 2"],
            "audio_duration": 120.5,
            "status": "stt_complete",
        })

        assert state["status"] == "stt_complete"
        assert len(state["transcript_segments"]) > 0
        assert state["audio_duration"] > 0

    def test_stt_to_summarized(self, stt_complete_state, sample_summary):
        """Test transition from STT to summarized."""
        state = stt_complete_state.copy()
        state.update({
            "draft_summary": sample_summary,
            "key_points": ["Point 1", "Point 2"],
            "decisions": ["Decision 1"],
            "status": "summarized",
        })

        assert state["status"] == "summarized"
        assert state["draft_summary"] != ""
        assert len(state["key_points"]) > 0

    def test_summarized_to_actions_extracted(self, summarized_state, sample_action_items):
        """Test transition to actions extracted."""
        state = summarized_state.copy()
        state.update({
            "action_items": sample_action_items,
            "status": "actions_extracted",
        })

        assert state["status"] == "actions_extracted"
        assert len(state["action_items"]) == 2

    def test_critique_passed(self, actions_extracted_state):
        """Test critique passing."""
        state = actions_extracted_state.copy()
        state.update({
            "critique": "Good summary with clear action items.",
            "critique_passed": True,
            "critique_issues": [],
            "requires_human_review": True,
            "status": "critique_complete",
        })

        assert state["critique_passed"] is True
        assert state["requires_human_review"] is True

    def test_critique_failed(self, actions_extracted_state):
        """Test critique failing."""
        state = actions_extracted_state.copy()
        state.update({
            "critique": "Summary missing key discussion points.",
            "critique_passed": False,
            "critique_issues": ["Missing context", "Unclear action items"],
            "retry_count": state["retry_count"] + 1,
            "status": "critique_complete",
        })

        assert state["critique_passed"] is False
        assert len(state["critique_issues"]) > 0
        assert state["retry_count"] == 1

    def test_human_approval(self, actions_extracted_state):
        """Test human approval flow."""
        state = actions_extracted_state.copy()
        state.update({
            "critique_passed": True,
            "human_approved": True,
            "final_summary": state["draft_summary"],
            "final_key_points": state["key_points"],
            "final_decisions": state["decisions"],
            "final_action_items": state["action_items"],
            "status": "completed",
            "completed_at": datetime.utcnow().isoformat(),
        })

        assert state["status"] == "completed"
        assert state["human_approved"] is True
        assert state["final_summary"] is not None
        assert state["completed_at"] is not None

    def test_failure_state(self, initial_state):
        """Test failure state."""
        state = initial_state.copy()
        state.update({
            "status": "failed",
            "error_message": "STT processing failed: Invalid audio format",
        })

        assert state["status"] == "failed"
        assert state["error_message"] is not None
