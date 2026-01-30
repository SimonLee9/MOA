"""
Upload API Tests
Tests for Tus protocol upload and processing endpoints
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
from httpx import AsyncClient

from app.models.meeting import Meeting, MeetingStatus


@pytest.mark.asyncio
async def test_start_processing_success(auth_client: AsyncClient, test_meeting: Meeting, tmp_path):
    """Test successful processing start."""
    # Create a mock file
    file_id = "test-file-123"

    with patch("app.api.v1.tus_upload.UPLOAD_DIR", tmp_path):
        # Create mock uploaded file
        test_file = tmp_path / file_id
        test_file.write_bytes(b"fake audio content")

        with patch("app.api.v1.tus_upload.trigger_langgraph_workflow") as mock_trigger:
            response = await auth_client.post(
                f"/api/v1/upload/meetings/{test_meeting.id}/process",
                params={"file_id": file_id}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "processing_started"
            assert data["meeting_id"] == str(test_meeting.id)
            assert "file_size" in data


@pytest.mark.asyncio
async def test_start_processing_meeting_not_found(auth_client: AsyncClient):
    """Test processing fails for non-existent meeting."""
    fake_id = uuid4()
    response = await auth_client.post(
        f"/api/v1/upload/meetings/{fake_id}/process",
        params={"file_id": "any-file"}
    )

    assert response.status_code == 404
    assert "Meeting not found" in response.json()["detail"]


@pytest.mark.asyncio
async def test_start_processing_file_not_found(auth_client: AsyncClient, test_meeting: Meeting, tmp_path):
    """Test processing fails when file doesn't exist."""
    with patch("app.api.v1.tus_upload.UPLOAD_DIR", tmp_path):
        response = await auth_client.post(
            f"/api/v1/upload/meetings/{test_meeting.id}/process",
            params={"file_id": "nonexistent-file"}
        )

        assert response.status_code == 404
        assert "file not found" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_start_processing_unauthenticated(client: AsyncClient, test_meeting: Meeting):
    """Test processing requires authentication."""
    response = await client.post(
        f"/api/v1/upload/meetings/{test_meeting.id}/process",
        params={"file_id": "test-file"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_processing_status_with_state(auth_client: AsyncClient, processing_meeting: Meeting):
    """Test getting processing status when state exists."""
    mock_state = AsyncMock()
    mock_state.values = {
        "status": "summarized",
        "requires_human_review": False,
        "raw_text": "Sample transcript",
        "draft_summary": "Sample summary",
        "action_items": [{"id": "1", "content": "Test"}],
        "critique": None,
        "error_message": None,
    }

    with patch("app.api.v1.tus_upload.create_meeting_graph") as mock_graph:
        mock_instance = AsyncMock()
        mock_instance.aget_state.return_value = mock_state
        mock_graph.return_value = mock_instance

        response = await auth_client.get(
            f"/api/v1/upload/meetings/{processing_meeting.id}/status"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "summarized"
        assert data["progress"]["stt_complete"] == True
        assert data["progress"]["summary_complete"] == True


@pytest.mark.asyncio
async def test_get_processing_status_no_state(auth_client: AsyncClient, test_meeting: Meeting):
    """Test getting processing status when no graph state exists."""
    with patch("app.api.v1.tus_upload.create_meeting_graph") as mock_graph:
        mock_instance = AsyncMock()
        mock_instance.aget_state.return_value = AsyncMock(values=None)
        mock_graph.return_value = mock_instance

        response = await auth_client.get(
            f"/api/v1/upload/meetings/{test_meeting.id}/status"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == test_meeting.status.value


@pytest.mark.asyncio
async def test_get_processing_status_graph_error(auth_client: AsyncClient, test_meeting: Meeting):
    """Test processing status handles graph errors gracefully."""
    with patch("app.api.v1.tus_upload.create_meeting_graph") as mock_graph:
        mock_graph.side_effect = Exception("Graph error")

        response = await auth_client.get(
            f"/api/v1/upload/meetings/{test_meeting.id}/status"
        )

        # Should fall back to database status
        assert response.status_code == 200
        data = response.json()
        assert "error" in data


@pytest.mark.asyncio
async def test_get_processing_status_not_found(auth_client: AsyncClient):
    """Test getting processing status for non-existent meeting."""
    fake_id = uuid4()
    response = await auth_client.get(f"/api/v1/upload/meetings/{fake_id}/status")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_processing_status_pending_review(auth_client: AsyncClient, processing_meeting: Meeting):
    """Test status shows pending review correctly."""
    mock_state = AsyncMock()
    mock_state.values = {
        "status": "pending_review",
        "requires_human_review": True,
        "raw_text": "Transcript",
        "draft_summary": "Summary",
        "action_items": [],
        "critique": "Review needed",
    }

    with patch("app.api.v1.tus_upload.create_meeting_graph") as mock_graph:
        mock_instance = AsyncMock()
        mock_instance.aget_state.return_value = mock_state
        mock_graph.return_value = mock_instance

        response = await auth_client.get(
            f"/api/v1/upload/meetings/{processing_meeting.id}/status"
        )

        assert response.status_code == 200
        data = response.json()
        assert data["requires_review"] == True
        assert data["progress"]["critique_complete"] == True
