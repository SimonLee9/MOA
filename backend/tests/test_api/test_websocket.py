"""
WebSocket API Tests
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.api.v1.websocket import (
    ConnectionManager,
    create_progress_message,
    ProgressType,
    send_progress_update,
)


class TestConnectionManager:
    """Tests for ConnectionManager class."""

    @pytest.fixture
    def manager(self):
        return ConnectionManager()

    @pytest.fixture
    def mock_websocket(self):
        ws = AsyncMock()
        ws.accept = AsyncMock()
        ws.send_json = AsyncMock()
        return ws

    @pytest.mark.asyncio
    async def test_connect(self, manager, mock_websocket):
        """Test connection registration."""
        meeting_id = "test-meeting-123"

        await manager.connect(mock_websocket, meeting_id)

        mock_websocket.accept.assert_called_once()
        assert manager.get_connection_count(meeting_id) == 1

    @pytest.mark.asyncio
    async def test_disconnect(self, manager, mock_websocket):
        """Test connection removal."""
        meeting_id = "test-meeting-123"

        await manager.connect(mock_websocket, meeting_id)
        assert manager.get_connection_count(meeting_id) == 1

        await manager.disconnect(mock_websocket, meeting_id)
        assert manager.get_connection_count(meeting_id) == 0

    @pytest.mark.asyncio
    async def test_broadcast(self, manager, mock_websocket):
        """Test message broadcasting."""
        meeting_id = "test-meeting-123"
        message = {"type": "test", "data": "hello"}

        await manager.connect(mock_websocket, meeting_id)
        await manager.broadcast(meeting_id, message)

        mock_websocket.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_to_multiple_clients(self, manager):
        """Test broadcasting to multiple connected clients."""
        meeting_id = "test-meeting-123"
        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()

        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.send_json = AsyncMock()

        await manager.connect(ws1, meeting_id)
        await manager.connect(ws2, meeting_id)

        message = {"type": "test", "data": "broadcast"}
        await manager.broadcast(meeting_id, message)

        ws1.send_json.assert_called_once_with(message)
        ws2.send_json.assert_called_once_with(message)

    @pytest.mark.asyncio
    async def test_broadcast_removes_disconnected_clients(self, manager):
        """Test that disconnected clients are cleaned up during broadcast."""
        meeting_id = "test-meeting-123"

        ws1 = AsyncMock()
        ws1.accept = AsyncMock()
        ws1.send_json = AsyncMock()  # Working client

        ws2 = AsyncMock()
        ws2.accept = AsyncMock()
        ws2.send_json.side_effect = Exception("Connection closed")  # Broken client

        await manager.connect(ws1, meeting_id)
        await manager.connect(ws2, meeting_id)

        assert manager.get_connection_count(meeting_id) == 2

        await manager.broadcast(meeting_id, {"type": "test"})

        # Broken client should be removed
        assert manager.get_connection_count(meeting_id) == 1

    @pytest.mark.asyncio
    async def test_broadcast_no_connections(self, manager):
        """Test broadcast with no connections does nothing."""
        meeting_id = "nonexistent-meeting"

        # Should not raise
        await manager.broadcast(meeting_id, {"type": "test"})

    @pytest.mark.asyncio
    async def test_multiple_meetings(self, manager):
        """Test connections for different meetings are separate."""
        meeting1 = "meeting-1"
        meeting2 = "meeting-2"

        ws1 = AsyncMock()
        ws1.accept = AsyncMock()

        ws2 = AsyncMock()
        ws2.accept = AsyncMock()

        await manager.connect(ws1, meeting1)
        await manager.connect(ws2, meeting2)

        assert manager.get_connection_count(meeting1) == 1
        assert manager.get_connection_count(meeting2) == 1


class TestProgressMessages:
    """Tests for progress message creation."""

    def test_create_progress_message_basic(self):
        """Test basic progress message creation."""
        message = create_progress_message(
            progress_type="test",
            progress=50,
            message="Test message",
        )

        assert message["type"] == "test"
        assert message["progress"] == 50
        assert message["message"] == "Test message"
        assert message["data"] == {}

    def test_create_progress_message_with_data(self):
        """Test progress message with additional data."""
        message = create_progress_message(
            progress_type="stt_complete",
            progress=40,
            message="STT done",
            data={"duration": 3600, "speakers": 3},
        )

        assert message["data"]["duration"] == 3600
        assert message["data"]["speakers"] == 3

    def test_progress_types(self):
        """Test all progress types are defined."""
        assert ProgressType.UPLOAD == "upload"
        assert ProgressType.STT_START == "stt_start"
        assert ProgressType.STT_PROGRESS == "stt_progress"
        assert ProgressType.STT_COMPLETE == "stt_complete"
        assert ProgressType.SUMMARIZE_START == "summarize_start"
        assert ProgressType.SUMMARIZE_COMPLETE == "summarize_complete"
        assert ProgressType.ACTIONS_START == "actions_start"
        assert ProgressType.ACTIONS_COMPLETE == "actions_complete"
        assert ProgressType.CRITIQUE_START == "critique_start"
        assert ProgressType.CRITIQUE_COMPLETE == "critique_complete"
        assert ProgressType.REVIEW_PENDING == "review_pending"
        assert ProgressType.APPROVED == "approved"
        assert ProgressType.COMPLETED == "completed"
        assert ProgressType.ERROR == "error"


class TestProgressBroadcasting:
    """Tests for progress broadcasting functions."""

    @pytest.mark.asyncio
    async def test_send_progress_update(self):
        """Test send_progress_update calls manager.broadcast."""
        with patch("app.api.v1.websocket.manager") as mock_manager:
            mock_manager.broadcast = AsyncMock()

            await send_progress_update(
                "meeting-123",
                ProgressType.STT_START,
                5,
                "Starting STT",
            )

            mock_manager.broadcast.assert_called_once()
            call_args = mock_manager.broadcast.call_args
            assert call_args[0][0] == "meeting-123"
            assert call_args[0][1]["type"] == "stt_start"
            assert call_args[0][1]["progress"] == 5

    @pytest.mark.asyncio
    async def test_broadcast_stt_start(self):
        """Test STT start broadcasting."""
        from app.api.v1.websocket import broadcast_stt_start

        with patch("app.api.v1.websocket.send_progress_update") as mock_send:
            mock_send.return_value = None

            await broadcast_stt_start("meeting-123")

            mock_send.assert_called_once()
            args, kwargs = mock_send.call_args
            assert args[0] == "meeting-123"
            assert args[1] == ProgressType.STT_START
            assert args[2] == 5  # Progress

    @pytest.mark.asyncio
    async def test_broadcast_stt_progress(self):
        """Test STT progress broadcasting with correct percentage mapping."""
        from app.api.v1.websocket import broadcast_stt_progress

        with patch("app.api.v1.websocket.send_progress_update") as mock_send:
            mock_send.return_value = None

            await broadcast_stt_progress("meeting-123", 50)

            mock_send.assert_called_once()
            args, kwargs = mock_send.call_args
            # 5 + int(50 * 0.35) = 5 + 17 = 22
            assert args[2] == 22

    @pytest.mark.asyncio
    async def test_broadcast_completed(self):
        """Test completion broadcasting."""
        from app.api.v1.websocket import broadcast_completed

        with patch("app.api.v1.websocket.send_progress_update") as mock_send:
            mock_send.return_value = None

            await broadcast_completed("meeting-123")

            mock_send.assert_called_once()
            args, kwargs = mock_send.call_args
            assert args[1] == ProgressType.COMPLETED
            assert args[2] == 100

    @pytest.mark.asyncio
    async def test_broadcast_error(self):
        """Test error broadcasting includes error message."""
        from app.api.v1.websocket import broadcast_error

        with patch("app.api.v1.websocket.send_progress_update") as mock_send:
            mock_send.return_value = None

            await broadcast_error("meeting-123", "Something went wrong")

            mock_send.assert_called_once()
            args, kwargs = mock_send.call_args
            assert args[1] == ProgressType.ERROR
            assert args[2] == 0  # Progress reset to 0
            assert "Something went wrong" in args[3]

    @pytest.mark.asyncio
    async def test_broadcast_critique_complete_passed(self):
        """Test critique complete when passed."""
        from app.api.v1.websocket import broadcast_critique_complete

        with patch("app.api.v1.websocket.send_progress_update") as mock_send:
            mock_send.return_value = None

            await broadcast_critique_complete("meeting-123", passed=True, retry_count=0)

            mock_send.assert_called_once()
            args, kwargs = mock_send.call_args
            assert args[2] == 90  # Progress at 90%

    @pytest.mark.asyncio
    async def test_broadcast_critique_complete_failed(self):
        """Test critique complete when failed (needs retry)."""
        from app.api.v1.websocket import broadcast_critique_complete

        with patch("app.api.v1.websocket.send_progress_update") as mock_send:
            mock_send.return_value = None

            await broadcast_critique_complete("meeting-123", passed=False, retry_count=1)

            mock_send.assert_called_once()
            args, kwargs = mock_send.call_args
            assert args[2] == 45  # Progress goes back to 45%
