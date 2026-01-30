"""
LangGraph Pipeline Tests
Tests for the main graph and node functions
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from datetime import datetime

from pipeline.graph import (
    stt_node,
    summarizer_node,
    action_extractor_node,
    critique_node,
    human_review_node,
    save_node,
    route_after_critique,
    route_after_human_review,
    route_after_stt,
)
from pipeline.state import create_initial_state, MeetingAgentState
from pipeline.errors import STTError, MaxRetriesExceededError


class TestSTTNode:
    """Test cases for STT node"""

    @pytest.mark.asyncio
    async def test_stt_success(self, initial_state, mock_clova_stt):
        """Test successful STT processing."""
        # Mock STT result
        mock_result = MagicMock()
        mock_result.segments = [
            MagicMock(speaker="김철수", text="안녕하세요", start_time=0.0, end_time=1.5, confidence=0.95),
            MagicMock(speaker="이영희", text="네, 안녕하세요", start_time=2.0, end_time=3.5, confidence=0.92),
        ]
        mock_result.speakers = ["김철수", "이영희"]
        mock_result.duration = 3.5

        with patch("pipeline.graph.transcribe_audio", return_value=mock_result):
            with patch("pipeline.graph.get_clova_client") as mock_client:
                mock_client.return_value.format_transcript.return_value = "김철수: 안녕하세요\n이영희: 네, 안녕하세요"

                result = await stt_node(initial_state)

                assert result["status"] == "stt_complete"
                assert len(result["transcript_segments"]) == 2
                assert result["speakers"] == ["김철수", "이영희"]
                assert result["audio_duration"] == 3.5

    @pytest.mark.asyncio
    async def test_stt_failure(self, initial_state):
        """Test STT node handles errors gracefully."""
        with patch("pipeline.graph.transcribe_audio") as mock_transcribe:
            mock_transcribe.side_effect = Exception("STT service unavailable")

            with patch("pipeline.graph.retry_async") as mock_retry:
                mock_retry.side_effect = MaxRetriesExceededError(
                    node="stt", attempts=3, last_error=Exception("STT failed")
                )

                result = await stt_node(initial_state)

                assert result["status"] == "failed"
                assert "error_message" in result


class TestSummarizerNode:
    """Test cases for Summarizer node"""

    @pytest.mark.asyncio
    async def test_summarizer_success(self, stt_complete_state, mock_claude_client):
        """Test successful summarization."""
        mock_summary_result = {
            "summary": "회의에서 다음 분기 계획을 논의했습니다.",
            "key_points": ["마케팅 예산 논의", "신제품 출시 일정"],
            "decisions": ["예산 20% 증액 승인"],
        }

        with patch("pipeline.graph.generate_summary", return_value=mock_summary_result):
            with patch("pipeline.graph.retry_async", return_value=mock_summary_result):
                result = await summarizer_node(stt_complete_state)

                assert result["status"] == "summarized"
                assert result["draft_summary"] == mock_summary_result["summary"]
                assert len(result["key_points"]) == 2
                assert len(result["decisions"]) == 1

    @pytest.mark.asyncio
    async def test_summarizer_with_feedback(self, stt_complete_state):
        """Test summarization with human feedback."""
        state = stt_complete_state.copy()
        state["human_feedback"] = "Please include more details about budget"
        state["retry_count"] = 1

        mock_result = {
            "summary": "Updated summary with budget details",
            "key_points": ["Budget increased by 20%"],
            "decisions": ["Budget approved"],
        }

        with patch("pipeline.graph.retry_async", return_value=mock_result):
            result = await summarizer_node(state)

            assert result["status"] == "summarized"


class TestActionExtractorNode:
    """Test cases for Action Extractor node"""

    @pytest.mark.asyncio
    async def test_extract_actions_success(self, summarized_state):
        """Test successful action extraction."""
        mock_actions = {
            "action_items": [
                {
                    "id": "act-1",
                    "content": "마케팅 계획서 작성",
                    "assignee": "이영희",
                    "due_date": "2024-01-22",
                    "priority": "high",
                    "status": "pending",
                },
                {
                    "id": "act-2",
                    "content": "개발팀 미팅 스케줄 조정",
                    "assignee": "박지민",
                    "due_date": "2024-01-25",
                    "priority": "medium",
                    "status": "pending",
                },
            ]
        }

        with patch("pipeline.graph.retry_async", return_value=mock_actions):
            result = await action_extractor_node(summarized_state)

            assert result["status"] == "actions_extracted"
            assert len(result["action_items"]) == 2
            assert result["action_items"][0]["assignee"] == "이영희"


class TestCritiqueNode:
    """Test cases for Critique node"""

    @pytest.mark.asyncio
    async def test_critique_passed(self, actions_extracted_state):
        """Test critique passes validation."""
        mock_critique = {
            "passed": True,
            "critique": "Summary is comprehensive and accurate.",
            "issues": [],
        }

        with patch("pipeline.graph.retry_async", return_value=mock_critique):
            result = await critique_node(actions_extracted_state)

            assert result["status"] == "critique_complete"
            assert result["critique_passed"] == True
            assert len(result["critique_issues"]) == 0

    @pytest.mark.asyncio
    async def test_critique_failed(self, actions_extracted_state):
        """Test critique fails validation."""
        mock_critique = {
            "passed": False,
            "critique": "Summary missing key discussion points.",
            "issues": ["Missing budget discussion", "Incomplete action items"],
        }

        with patch("pipeline.graph.retry_async", return_value=mock_critique):
            result = await critique_node(actions_extracted_state)

            assert result["status"] == "critique_complete"
            assert result["critique_passed"] == False
            assert len(result["critique_issues"]) == 2

    @pytest.mark.asyncio
    async def test_critique_error_graceful(self, actions_extracted_state):
        """Test critique handles errors gracefully and allows progress."""
        with patch("pipeline.graph.retry_async") as mock_retry:
            mock_retry.side_effect = Exception("Critique service error")

            result = await critique_node(actions_extracted_state)

            # Should allow progress despite error
            assert result["status"] == "critique_complete"
            assert result["critique_passed"] == True


class TestHumanReviewNode:
    """Test cases for Human Review node"""

    @pytest.mark.asyncio
    async def test_human_review_approve(self, actions_extracted_state):
        """Test human review approval."""
        state = actions_extracted_state.copy()
        state["critique"] = "Looks good"
        state["critique_passed"] = True

        user_decision = {
            "action": "approve",
            "feedback": "Approved as is",
        }

        with patch("pipeline.graph.interrupt", return_value=user_decision):
            result = await human_review_node(state)

            assert result["human_approved"] == True
            assert result["status"] == "approved"
            assert result["final_summary"] is not None

    @pytest.mark.asyncio
    async def test_human_review_approve_with_changes(self, actions_extracted_state):
        """Test human review approval with modifications."""
        state = actions_extracted_state.copy()
        state["critique"] = "Minor issues"
        state["critique_passed"] = True

        user_decision = {
            "action": "approve",
            "feedback": "Modified summary",
            "updated_summary": "New updated summary",
            "updated_actions": [{"id": "new-1", "content": "New action"}],
        }

        with patch("pipeline.graph.interrupt", return_value=user_decision):
            result = await human_review_node(state)

            assert result["human_approved"] == True
            assert result["final_summary"] == "New updated summary"

    @pytest.mark.asyncio
    async def test_human_review_reject(self, actions_extracted_state):
        """Test human review rejection."""
        state = actions_extracted_state.copy()
        state["critique"] = "Issues found"
        state["critique_passed"] = True
        state["retry_count"] = 0

        user_decision = {
            "action": "reject",
            "feedback": "Missing key discussion about Q2 plans",
        }

        with patch("pipeline.graph.interrupt", return_value=user_decision):
            result = await human_review_node(state)

            assert result["human_approved"] == False
            assert result["status"] == "revision_requested"
            assert result["human_feedback"] == "Missing key discussion about Q2 plans"
            assert result["retry_count"] == 1


class TestSaveNode:
    """Test cases for Save node"""

    @pytest.mark.asyncio
    async def test_save_success(self, actions_extracted_state):
        """Test successful save."""
        state = actions_extracted_state.copy()
        state["final_summary"] = "Final summary"
        state["final_action_items"] = []
        state["human_approved"] = True

        result = await save_node(state)

        assert result["status"] == "completed"
        assert result["human_approved"] == True
        assert "completed_at" in result


class TestRoutingFunctions:
    """Test cases for routing functions"""

    def test_route_after_stt_success(self):
        """Test routing after successful STT."""
        state = {"status": "stt_complete"}
        assert route_after_stt(state) == "summarizer"

    def test_route_after_stt_failure(self):
        """Test routing after failed STT."""
        state = {"status": "failed"}
        assert route_after_stt(state) == "end"

    def test_route_after_critique_passed(self):
        """Test routing when critique passes."""
        state = {"critique_passed": True, "retry_count": 0}
        assert route_after_critique(state) == "human_review"

    def test_route_after_critique_failed_can_retry(self):
        """Test routing when critique fails but can retry."""
        state = {"critique_passed": False, "retry_count": 1}
        assert route_after_critique(state) == "summarizer"

    def test_route_after_critique_failed_max_retries(self):
        """Test routing when critique fails at max retries."""
        state = {"critique_passed": False, "retry_count": 3}
        assert route_after_critique(state) == "human_review"

    def test_route_after_critique_system_error(self):
        """Test routing after system error."""
        state = {"status": "failed", "critique_passed": False}
        assert route_after_critique(state) == "end"

    def test_route_after_human_review_approved(self):
        """Test routing when human approves."""
        state = {"human_approved": True}
        assert route_after_human_review(state) == "save"

    def test_route_after_human_review_rejected_can_retry(self):
        """Test routing when human rejects but can retry."""
        state = {"human_approved": False, "retry_count": 2}
        assert route_after_human_review(state) == "summarizer"

    def test_route_after_human_review_rejected_max_retries(self):
        """Test routing when human rejects at max retries."""
        state = {"human_approved": False, "retry_count": 5}
        assert route_after_human_review(state) == "end"


class TestGraphIntegration:
    """Integration tests for graph creation"""

    @pytest.mark.asyncio
    async def test_create_meeting_graph(self):
        """Test graph creation succeeds."""
        with patch("pipeline.graph.get_checkpointer") as mock_checkpointer:
            mock_checkpointer.return_value = MagicMock()

            from pipeline.graph import create_meeting_graph

            graph = await create_meeting_graph()

            assert graph is not None
