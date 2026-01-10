"""
Review API Tests
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

from app.models.meeting import Meeting, MeetingStatus


@pytest.mark.asyncio
async def test_get_review_status_no_review(auth_client: AsyncClient, test_meeting: Meeting):
    """Test getting review status when no review pending."""
    with patch("app.api.v1.review.create_meeting_graph") as mock_graph:
        mock_instance = AsyncMock()
        mock_instance.aget_state.return_value = AsyncMock(
            values={"status": "processing", "requires_human_review": False}
        )
        mock_graph.return_value = mock_instance

        response = await auth_client.get(f"/api/v1/meetings/{test_meeting.id}/review")

        assert response.status_code == 200
        data = response.json()
        assert data["requires_review"] == False


@pytest.mark.asyncio
async def test_get_review_status_with_review(auth_client: AsyncClient, test_meeting: Meeting):
    """Test getting review status when review is pending."""
    with patch("app.api.v1.review.create_meeting_graph") as mock_graph:
        mock_instance = AsyncMock()
        mock_instance.aget_state.return_value = AsyncMock(
            values={
                "status": "review_pending",
                "requires_human_review": True,
                "draft_summary": "Meeting summary here",
                "key_points": ["Point 1", "Point 2"],
                "decisions": ["Decision 1"],
                "action_items": [{"content": "Action 1"}],
                "critique": "Review needed",
                "retry_count": 0
            }
        )
        mock_graph.return_value = mock_instance

        response = await auth_client.get(f"/api/v1/meetings/{test_meeting.id}/review")

        assert response.status_code == 200
        data = response.json()
        assert data["requires_review"] == True
        assert data["review_data"]["minutes"] == "Meeting summary here"
        assert len(data["review_data"]["key_points"]) == 2


@pytest.mark.asyncio
async def test_get_review_status_not_found(auth_client: AsyncClient):
    """Test getting review status for non-existent meeting."""
    fake_id = uuid4()
    response = await auth_client.get(f"/api/v1/meetings/{fake_id}/review")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_submit_review_approve(auth_client: AsyncClient, test_meeting: Meeting):
    """Test submitting approval review."""
    with patch("app.api.v1.review.resume_after_review") as mock_resume:
        mock_resume.return_value = {"status": "completed"}

        response = await auth_client.post(
            f"/api/v1/meetings/{test_meeting.id}/review",
            json={
                "action": "approve",
                "feedback": None
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "approve"
        assert "approved" in data["message"]


@pytest.mark.asyncio
async def test_submit_review_reject(auth_client: AsyncClient, test_meeting: Meeting):
    """Test submitting rejection review."""
    with patch("app.api.v1.review.resume_after_review") as mock_resume:
        mock_resume.return_value = {"status": "processing"}

        response = await auth_client.post(
            f"/api/v1/meetings/{test_meeting.id}/review",
            json={
                "action": "reject",
                "feedback": "Summary lacks key discussion points"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["action"] == "reject"


@pytest.mark.asyncio
async def test_submit_review_with_updates(auth_client: AsyncClient, test_meeting: Meeting):
    """Test submitting review with manual updates."""
    with patch("app.api.v1.review.resume_after_review") as mock_resume:
        mock_resume.return_value = {"status": "completed"}

        response = await auth_client.post(
            f"/api/v1/meetings/{test_meeting.id}/review",
            json={
                "action": "approve",
                "updated_summary": "Updated summary text",
                "updated_key_points": ["New point 1", "New point 2"],
                "updated_decisions": ["New decision"],
                "updated_actions": [
                    {
                        "id": "action-1",
                        "content": "Updated action",
                        "assignee": "john@example.com",
                        "priority": "high",
                        "status": "approved"
                    }
                ]
            }
        )

        assert response.status_code == 200

        # Verify resume_after_review was called with correct args
        mock_resume.assert_called_once()
        call_kwargs = mock_resume.call_args.kwargs
        assert call_kwargs["updated_summary"] == "Updated summary text"
        assert len(call_kwargs["updated_key_points"]) == 2


@pytest.mark.asyncio
async def test_submit_review_not_found(auth_client: AsyncClient):
    """Test submitting review for non-existent meeting."""
    fake_id = uuid4()
    response = await auth_client.post(
        f"/api/v1/meetings/{fake_id}/review",
        json={"action": "approve"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_results_completed(auth_client: AsyncClient, completed_meeting: Meeting):
    """Test getting results for completed meeting."""
    with patch("app.api.v1.review.create_meeting_graph") as mock_graph:
        mock_instance = AsyncMock()
        mock_instance.aget_state.return_value = AsyncMock(
            values={
                "status": "completed",
                "final_summary": "Final meeting summary",
                "final_key_points": ["Key point 1"],
                "final_decisions": ["Decision 1"],
                "final_action_items": [{"content": "Action 1"}],
                "execution_results": [],
                "human_approved": True,
                "completed_at": "2024-01-15T12:00:00Z"
            }
        )
        mock_graph.return_value = mock_instance

        response = await auth_client.get(f"/api/v1/meetings/{completed_meeting.id}/results")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["summary"] == "Final meeting summary"
        assert data["human_approved"] == True


@pytest.mark.asyncio
async def test_get_results_not_completed(auth_client: AsyncClient, processing_meeting: Meeting):
    """Test getting results for non-completed meeting."""
    with patch("app.api.v1.review.create_meeting_graph") as mock_graph:
        mock_instance = AsyncMock()
        mock_instance.aget_state.return_value = AsyncMock(
            values={"status": "processing"}
        )
        mock_graph.return_value = mock_instance

        response = await auth_client.get(f"/api/v1/meetings/{processing_meeting.id}/results")

        assert response.status_code == 400
        assert "not completed" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_results_no_state(auth_client: AsyncClient, test_meeting: Meeting):
    """Test getting results when no state exists."""
    with patch("app.api.v1.review.create_meeting_graph") as mock_graph:
        mock_instance = AsyncMock()
        mock_instance.aget_state.return_value = AsyncMock(values=None)
        mock_graph.return_value = mock_instance

        response = await auth_client.get(f"/api/v1/meetings/{test_meeting.id}/results")

        assert response.status_code == 404


@pytest.mark.asyncio
async def test_review_unauthenticated(client: AsyncClient, test_meeting: Meeting):
    """Test review endpoints require authentication."""
    # Get status
    response = await client.get(f"/api/v1/meetings/{test_meeting.id}/review")
    assert response.status_code == 401

    # Submit review
    response = await client.post(
        f"/api/v1/meetings/{test_meeting.id}/review",
        json={"action": "approve"}
    )
    assert response.status_code == 401

    # Get results
    response = await client.get(f"/api/v1/meetings/{test_meeting.id}/results")
    assert response.status_code == 401
