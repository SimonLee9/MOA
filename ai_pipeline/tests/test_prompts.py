"""
Tests for LLM Prompts
"""

import pytest

from pipeline.prompts.summarize import (
    SUMMARY_SYSTEM_PROMPT,
    SUMMARY_USER_PROMPT,
    SUMMARY_SHORT_PROMPT,
)
from pipeline.prompts.extract_actions import (
    ACTION_SYSTEM_PROMPT,
    ACTION_USER_PROMPT,
    format_action_system_prompt,
)
from pipeline.prompts.critique import (
    CRITIQUE_SYSTEM_PROMPT,
    CRITIQUE_USER_PROMPT,
)


class TestSummarizePrompts:
    """Tests for summarization prompts."""

    def test_system_prompt_exists(self):
        """Test system prompt is defined."""
        assert SUMMARY_SYSTEM_PROMPT is not None
        assert len(SUMMARY_SYSTEM_PROMPT) > 0

    def test_system_prompt_mentions_json(self):
        """Test system prompt requests JSON output."""
        assert "JSON" in SUMMARY_SYSTEM_PROMPT or "json" in SUMMARY_SYSTEM_PROMPT

    def test_system_prompt_includes_output_fields(self):
        """Test system prompt specifies required fields."""
        assert "summary" in SUMMARY_SYSTEM_PROMPT
        assert "key_points" in SUMMARY_SYSTEM_PROMPT
        assert "decisions" in SUMMARY_SYSTEM_PROMPT

    def test_user_prompt_has_placeholders(self):
        """Test user prompt has required placeholders."""
        assert "{meeting_title}" in SUMMARY_USER_PROMPT
        assert "{meeting_date}" in SUMMARY_USER_PROMPT
        assert "{speakers}" in SUMMARY_USER_PROMPT
        assert "{transcript}" in SUMMARY_USER_PROMPT

    def test_user_prompt_can_be_formatted(self):
        """Test user prompt can be formatted with values."""
        formatted = SUMMARY_USER_PROMPT.format(
            meeting_title="Test Meeting",
            meeting_date="2024-01-15",
            speakers="A, B, C",
            transcript="Test transcript content",
        )

        assert "Test Meeting" in formatted
        assert "2024-01-15" in formatted
        assert "A, B, C" in formatted
        assert "Test transcript content" in formatted

    def test_short_prompt_exists(self):
        """Test short meeting prompt exists."""
        assert SUMMARY_SHORT_PROMPT is not None
        assert "{transcript}" in SUMMARY_SHORT_PROMPT


class TestExtractActionsPrompts:
    """Tests for action extraction prompts."""

    def test_system_prompt_exists(self):
        """Test system prompt is defined."""
        assert ACTION_SYSTEM_PROMPT is not None
        assert len(ACTION_SYSTEM_PROMPT) > 0

    def test_system_prompt_mentions_action_items(self):
        """Test system prompt mentions action items."""
        assert "액션" in ACTION_SYSTEM_PROMPT or "action" in ACTION_SYSTEM_PROMPT.lower()

    def test_system_prompt_defines_priority(self):
        """Test system prompt defines priority levels."""
        prompt = ACTION_SYSTEM_PROMPT.lower()
        assert "priority" in prompt or "우선순위" in ACTION_SYSTEM_PROMPT

    def test_user_prompt_has_required_placeholders(self):
        """Test user prompt has all required placeholders."""
        assert "{meeting_title}" in ACTION_USER_PROMPT
        assert "{transcript}" in ACTION_USER_PROMPT
        assert "{summary}" in ACTION_USER_PROMPT

    def test_format_action_system_prompt(self):
        """Test format_action_system_prompt function."""
        result = format_action_system_prompt()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_user_prompt_includes_context(self):
        """Test user prompt includes both transcript and summary."""
        formatted = ACTION_USER_PROMPT.format(
            meeting_title="Test",
            meeting_date="2024-01-15",
            speakers="A, B",
            transcript="Transcript here",
            summary="Summary here",
        )

        assert "Transcript here" in formatted
        assert "Summary here" in formatted


class TestCritiquePrompts:
    """Tests for critique prompts."""

    def test_system_prompt_exists(self):
        """Test system prompt is defined."""
        assert CRITIQUE_SYSTEM_PROMPT is not None
        assert len(CRITIQUE_SYSTEM_PROMPT) > 0

    def test_system_prompt_mentions_evaluation(self):
        """Test system prompt mentions evaluation criteria."""
        prompt = CRITIQUE_SYSTEM_PROMPT.lower()
        assert "평가" in CRITIQUE_SYSTEM_PROMPT or "evaluat" in prompt or "검증" in CRITIQUE_SYSTEM_PROMPT

    def test_system_prompt_defines_output_format(self):
        """Test system prompt defines JSON output."""
        assert "passed" in CRITIQUE_SYSTEM_PROMPT or "합격" in CRITIQUE_SYSTEM_PROMPT

    def test_user_prompt_has_all_inputs(self):
        """Test user prompt accepts all generated content."""
        assert "{transcript}" in CRITIQUE_USER_PROMPT
        assert "{summary}" in CRITIQUE_USER_PROMPT
        assert "{key_points}" in CRITIQUE_USER_PROMPT
        assert "{decisions}" in CRITIQUE_USER_PROMPT
        assert "{action_items}" in CRITIQUE_USER_PROMPT

    def test_user_prompt_can_be_formatted(self):
        """Test user prompt can be formatted."""
        formatted = CRITIQUE_USER_PROMPT.format(
            transcript="Original transcript",
            summary="Generated summary",
            key_points="- Point 1\n- Point 2",
            decisions="- Decision 1",
            action_items='[{"id": "1", "content": "Action"}]',
        )

        assert "Original transcript" in formatted
        assert "Generated summary" in formatted
        assert "Point 1" in formatted


class TestPromptQuality:
    """Tests for prompt quality and consistency."""

    def test_all_prompts_use_korean(self):
        """Test prompts are in Korean as per project requirements."""
        # At least some Korean characters should be present
        assert any('\uac00' <= c <= '\ud7a3' for c in SUMMARY_SYSTEM_PROMPT)
        assert any('\uac00' <= c <= '\ud7a3' for c in ACTION_SYSTEM_PROMPT)
        assert any('\uac00' <= c <= '\ud7a3' for c in CRITIQUE_SYSTEM_PROMPT)

    def test_prompts_request_structured_output(self):
        """Test all prompts request JSON output."""
        assert "json" in SUMMARY_SYSTEM_PROMPT.lower()
        assert "json" in ACTION_SYSTEM_PROMPT.lower()
        assert "json" in CRITIQUE_SYSTEM_PROMPT.lower()

    def test_summary_prompt_excludes_chitchat(self):
        """Test summary prompt instructs to exclude chitchat."""
        assert "잡담" in SUMMARY_SYSTEM_PROMPT or "인사" in SUMMARY_SYSTEM_PROMPT

    def test_action_prompt_includes_assignee(self):
        """Test action prompt mentions assignee."""
        assert "assignee" in ACTION_SYSTEM_PROMPT.lower() or "담당" in ACTION_SYSTEM_PROMPT

    def test_critique_prompt_has_quality_criteria(self):
        """Test critique prompt has evaluation criteria."""
        # Should mention issues/problems/criteria
        prompt = CRITIQUE_SYSTEM_PROMPT.lower()
        assert (
            "issues" in prompt
            or "문제" in CRITIQUE_SYSTEM_PROMPT
            or "기준" in CRITIQUE_SYSTEM_PROMPT
            or "검증" in CRITIQUE_SYSTEM_PROMPT
        )
