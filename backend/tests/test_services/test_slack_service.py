"""
Slack Service Tests
Tests for Slack notification integration
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.slack_service import SlackService


@pytest.fixture
def slack_service():
    """Create a Slack service with test webhook URL."""
    return SlackService(webhook_url="https://hooks.slack.com/test")


@pytest.fixture
def disabled_slack_service():
    """Create a disabled Slack service (no webhook)."""
    return SlackService(webhook_url=None)


class TestSlackService:
    """Test cases for SlackService"""

    @pytest.mark.asyncio
    async def test_send_message_success(self, slack_service):
        """Test successful message sending."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await slack_service.send_message("Test message")

            assert result == True
            mock_client.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_disabled(self, disabled_slack_service):
        """Test message sending when Slack is disabled."""
        result = await disabled_slack_service.send_message("Test message")

        assert result == False

    @pytest.mark.asyncio
    async def test_send_message_with_channel(self, slack_service):
        """Test message sending to specific channel."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await slack_service.send_message(
                "Test message",
                channel="#test-channel"
            )

            assert result == True
            call_kwargs = mock_client.post.call_args
            assert call_kwargs[1]["json"]["channel"] == "#test-channel"

    @pytest.mark.asyncio
    async def test_send_message_with_blocks(self, slack_service):
        """Test message sending with blocks."""
        blocks = [{"type": "section", "text": {"type": "plain_text", "text": "Test"}}]

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await slack_service.send_message("Test", blocks=blocks)

            assert result == True
            call_kwargs = mock_client.post.call_args
            assert call_kwargs[1]["json"]["blocks"] == blocks

    @pytest.mark.asyncio
    async def test_send_message_network_error(self, slack_service):
        """Test message sending handles network errors."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.ConnectError("Network error")
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await slack_service.send_message("Test message")

            assert result == False

    @pytest.mark.asyncio
    async def test_send_review_notification(self, slack_service):
        """Test review notification sending."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await slack_service.send_review_notification(
                meeting_title="Sprint Planning",
                meeting_id="123",
                meeting_url="https://moa.ai/meetings/123"
            )

            assert result == True
            call_kwargs = mock_client.post.call_args
            payload = call_kwargs[1]["json"]
            assert "회의 검토 요청" in str(payload["blocks"])
            assert "Sprint Planning" in str(payload["blocks"])

    @pytest.mark.asyncio
    async def test_send_processing_complete(self, slack_service):
        """Test processing complete notification."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await slack_service.send_processing_complete(
                meeting_title="Weekly Standup",
                meeting_url="https://moa.ai/meetings/456",
                summary_preview="This meeting discussed...",
                action_items_count=3
            )

            assert result == True
            call_kwargs = mock_client.post.call_args
            payload = call_kwargs[1]["json"]
            assert "회의 처리 완료" in str(payload["blocks"])
            assert "3개" in str(payload["blocks"])

    @pytest.mark.asyncio
    async def test_send_processing_failed(self, slack_service):
        """Test processing failed notification."""
        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await slack_service.send_processing_failed(
                meeting_title="Failed Meeting",
                meeting_url="https://moa.ai/meetings/789",
                error_message="STT service timeout"
            )

            assert result == True
            call_kwargs = mock_client.post.call_args
            payload = call_kwargs[1]["json"]
            assert "회의 처리 실패" in str(payload["blocks"])
            assert "STT service timeout" in str(payload["blocks"])

    @pytest.mark.asyncio
    async def test_send_action_item_reminder(self, slack_service):
        """Test action item reminder notification."""
        due_date = datetime(2024, 1, 25, 14, 0, 0)

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__.return_value = mock_client
            mock_client.__aexit__.return_value = None
            mock_client_class.return_value = mock_client

            result = await slack_service.send_action_item_reminder(
                assignee="김철수",
                action_content="마케팅 계획서 제출",
                due_date=due_date,
                meeting_title="분기 계획 회의",
                meeting_url="https://moa.ai/meetings/101"
            )

            assert result == True
            call_kwargs = mock_client.post.call_args
            payload = call_kwargs[1]["json"]
            assert "액션 아이템 마감 알림" in str(payload["blocks"])
            assert "김철수" in str(payload["blocks"])
            assert "2024년 01월 25일" in str(payload["blocks"])


class TestSlackServiceInitialization:
    """Test Slack service initialization"""

    def test_enabled_with_webhook(self):
        """Test service is enabled when webhook is provided."""
        service = SlackService(webhook_url="https://hooks.slack.com/test")
        assert service.enabled == True

    def test_disabled_without_webhook(self):
        """Test service is disabled when no webhook."""
        service = SlackService(webhook_url=None)
        assert service.enabled == False

    def test_disabled_with_empty_webhook(self):
        """Test service is disabled with empty webhook."""
        service = SlackService(webhook_url="")
        assert service.enabled == False
