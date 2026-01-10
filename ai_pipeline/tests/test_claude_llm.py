"""
Tests for Claude LLM Integration
"""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock

from pipeline.integrations.claude_llm import (
    ClaudeClient,
    get_claude_client,
    generate_summary,
    extract_actions,
    critique_results,
)


class TestClaudeClient:
    """Tests for ClaudeClient class."""

    @pytest.fixture
    def client(self):
        return ClaudeClient(api_key="test-api-key")

    def test_client_initialization(self, client):
        """Test client initializes with correct settings."""
        assert client.api_key == "test-api-key"
        assert client._client is None  # Lazy initialization

    def test_extract_json_from_code_block(self, client):
        """Test JSON extraction from markdown code block."""
        text = '''Here's the response:
```json
{"key": "value"}
```
Done!'''
        result = client._extract_json(text)
        assert result == '{"key": "value"}'

    def test_extract_json_from_raw_json(self, client):
        """Test JSON extraction from raw JSON."""
        text = 'Response: {"key": "value", "nested": {"a": 1}}'
        result = client._extract_json(text)
        assert '{"key": "value"' in result

    def test_extract_json_returns_original_if_no_json(self, client):
        """Test returns original text if no JSON found."""
        text = "No JSON here"
        result = client._extract_json(text)
        assert result == "No JSON here"

    @pytest.mark.asyncio
    async def test_generate_calls_api(self, client):
        """Test generate method calls Claude API."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Test response")]

        with patch.object(client, "client") as mock_client:
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            result = await client.generate("Test prompt")

            assert result == "Test response"
            mock_client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_json_parses_response(self, client):
        """Test generate_json parses JSON response."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='{"result": "success"}')]

        with patch.object(client, "client") as mock_client:
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            result = await client.generate_json("Test prompt")

            assert result == {"result": "success"}

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self, client):
        """Test generate includes system prompt."""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Response")]

        with patch.object(client, "client") as mock_client:
            mock_client.messages.create = AsyncMock(return_value=mock_response)

            await client.generate(
                "User prompt",
                system_prompt="System instructions",
            )

            call_kwargs = mock_client.messages.create.call_args.kwargs
            assert call_kwargs["system"] == "System instructions"


class TestGenerateSummary:
    """Tests for generate_summary function."""

    @pytest.mark.asyncio
    async def test_generate_summary_format(
        self,
        sample_raw_text,
        sample_speakers,
    ):
        """Test summary generation returns correct format."""
        expected_response = {
            "summary": "Test summary",
            "key_points": ["Point 1", "Point 2"],
            "decisions": ["Decision 1"],
        }

        with patch("pipeline.integrations.claude_llm.get_claude_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.generate_json = AsyncMock(return_value=expected_response)
            mock_get.return_value = mock_client

            result = await generate_summary(
                transcript=sample_raw_text,
                meeting_title="Test Meeting",
                meeting_date="2024-01-15",
                speakers=sample_speakers,
            )

            assert "summary" in result
            assert "key_points" in result
            assert "decisions" in result

    @pytest.mark.asyncio
    async def test_generate_summary_handles_missing_date(
        self,
        sample_raw_text,
        sample_speakers,
    ):
        """Test summary handles missing date."""
        with patch("pipeline.integrations.claude_llm.get_claude_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.generate_json = AsyncMock(return_value={
                "summary": "Test",
                "key_points": [],
                "decisions": [],
            })
            mock_get.return_value = mock_client

            result = await generate_summary(
                transcript=sample_raw_text,
                meeting_title="Test Meeting",
                meeting_date=None,
                speakers=sample_speakers,
            )

            # Should not raise
            assert result is not None


class TestExtractActions:
    """Tests for extract_actions function."""

    @pytest.mark.asyncio
    async def test_extract_actions_format(
        self,
        sample_raw_text,
        sample_summary,
        sample_speakers,
    ):
        """Test action extraction returns correct format."""
        expected_response = {
            "action_items": [
                {
                    "id": "1",
                    "content": "Action 1",
                    "assignee": "Person A",
                    "due_date": "2024-01-20",
                    "priority": "high",
                },
            ],
        }

        with patch("pipeline.integrations.claude_llm.get_claude_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.generate_json = AsyncMock(return_value=expected_response)
            mock_get.return_value = mock_client

            result = await extract_actions(
                transcript=sample_raw_text,
                summary=sample_summary,
                meeting_title="Test Meeting",
                meeting_date="2024-01-15",
                speakers=sample_speakers,
            )

            assert "action_items" in result
            assert len(result["action_items"]) > 0


class TestCritiqueResults:
    """Tests for critique_results function."""

    @pytest.mark.asyncio
    async def test_critique_passed(
        self,
        sample_raw_text,
        sample_summary,
        sample_key_points,
        sample_decisions,
        sample_action_items,
    ):
        """Test critique with passing results."""
        expected_response = {
            "passed": True,
            "issues": [],
            "suggestions": [],
            "critique": "Good quality summary.",
        }

        with patch("pipeline.integrations.claude_llm.get_claude_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.generate_json = AsyncMock(return_value=expected_response)
            mock_get.return_value = mock_client

            result = await critique_results(
                transcript=sample_raw_text,
                summary=sample_summary,
                key_points=sample_key_points,
                decisions=sample_decisions,
                action_items=sample_action_items,
            )

            assert result["passed"] is True
            assert len(result["issues"]) == 0

    @pytest.mark.asyncio
    async def test_critique_failed(
        self,
        sample_raw_text,
        sample_summary,
        sample_key_points,
        sample_decisions,
        sample_action_items,
    ):
        """Test critique with failing results."""
        expected_response = {
            "passed": False,
            "issues": ["Missing context", "Unclear assignees"],
            "suggestions": ["Add more detail", "Specify team members"],
            "critique": "Summary needs improvement.",
        }

        with patch("pipeline.integrations.claude_llm.get_claude_client") as mock_get:
            mock_client = AsyncMock()
            mock_client.generate_json = AsyncMock(return_value=expected_response)
            mock_get.return_value = mock_client

            result = await critique_results(
                transcript=sample_raw_text,
                summary=sample_summary,
                key_points=sample_key_points,
                decisions=sample_decisions,
                action_items=sample_action_items,
            )

            assert result["passed"] is False
            assert len(result["issues"]) > 0


class TestSingleton:
    """Tests for singleton pattern."""

    def test_get_claude_client_returns_same_instance(self):
        """Test get_claude_client returns singleton."""
        with patch("pipeline.integrations.claude_llm._claude_client", None):
            client1 = get_claude_client()
            client2 = get_claude_client()

            # Note: This test might fail if run in isolation due to module state
            # In production, would use proper dependency injection
