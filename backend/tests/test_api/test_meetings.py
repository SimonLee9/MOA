"""
Meetings API Tests
"""

import pytest
from uuid import uuid4
from httpx import AsyncClient

from app.models.meeting import Meeting, MeetingStatus


@pytest.mark.asyncio
async def test_create_meeting(auth_client: AsyncClient):
    """Test meeting creation."""
    response = await auth_client.post(
        "/api/v1/meetings",
        json={
            "title": "Sprint Planning",
            "meeting_date": "2024-01-15T10:00:00Z"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Sprint Planning"
    assert data["status"] == "uploaded"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_meeting_unauthenticated(client: AsyncClient):
    """Test meeting creation fails without auth."""
    response = await client.post(
        "/api/v1/meetings",
        json={"title": "Test Meeting"}
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_meetings(auth_client: AsyncClient, test_meeting: Meeting):
    """Test meeting list retrieval."""
    response = await auth_client.get("/api/v1/meetings")

    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1


@pytest.mark.asyncio
async def test_list_meetings_pagination(auth_client: AsyncClient, test_meeting: Meeting):
    """Test meeting list pagination."""
    response = await auth_client.get("/api/v1/meetings?page=1&size=5")

    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["size"] == 5


@pytest.mark.asyncio
async def test_get_meeting(auth_client: AsyncClient, test_meeting: Meeting):
    """Test getting single meeting."""
    response = await auth_client.get(f"/api/v1/meetings/{test_meeting.id}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(test_meeting.id)
    assert data["title"] == test_meeting.title


@pytest.mark.asyncio
async def test_get_meeting_not_found(auth_client: AsyncClient):
    """Test getting non-existent meeting."""
    fake_id = uuid4()
    response = await auth_client.get(f"/api/v1/meetings/{fake_id}")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_meeting(auth_client: AsyncClient, test_meeting: Meeting):
    """Test meeting update."""
    response = await auth_client.patch(
        f"/api/v1/meetings/{test_meeting.id}",
        json={"title": "Updated Meeting Title"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Meeting Title"


@pytest.mark.asyncio
async def test_delete_meeting(auth_client: AsyncClient, test_meeting: Meeting):
    """Test meeting deletion."""
    response = await auth_client.delete(f"/api/v1/meetings/{test_meeting.id}")
    assert response.status_code == 204

    # Verify deletion
    get_response = await auth_client.get(f"/api/v1/meetings/{test_meeting.id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_get_processing_status(auth_client: AsyncClient, processing_meeting: Meeting):
    """Test getting processing status."""
    response = await auth_client.get(f"/api/v1/meetings/{processing_meeting.id}/process/status")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "processing"
    assert "progress" in data


@pytest.mark.asyncio
async def test_get_action_items_empty(auth_client: AsyncClient, test_meeting: Meeting):
    """Test getting action items (empty)."""
    response = await auth_client.get(f"/api/v1/meetings/{test_meeting.id}/actions")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_create_action_item(auth_client: AsyncClient, test_meeting: Meeting):
    """Test manual action item creation."""
    response = await auth_client.post(
        f"/api/v1/meetings/{test_meeting.id}/actions",
        json={
            "content": "Complete project proposal",
            "assignee": "john@example.com",
            "priority": "high"
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["content"] == "Complete project proposal"
    assert data["priority"] == "high"


@pytest.mark.asyncio
async def test_update_action_item(auth_client: AsyncClient, test_meeting: Meeting, db_session):
    """Test action item update."""
    # Create action item first
    from app.models.meeting import ActionItem
    from uuid import uuid4

    action_item = ActionItem(
        id=uuid4(),
        meeting_id=test_meeting.id,
        content="Original content",
        priority="medium"
    )
    db_session.add(action_item)
    await db_session.commit()

    # Update it
    response = await auth_client.put(
        f"/api/v1/meetings/{test_meeting.id}/actions/{action_item.id}",
        json={
            "content": "Updated content",
            "status": "completed"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["content"] == "Updated content"
    assert data["status"] == "completed"


@pytest.mark.asyncio
async def test_delete_action_item(auth_client: AsyncClient, test_meeting: Meeting, db_session):
    """Test action item deletion."""
    from app.models.meeting import ActionItem
    from uuid import uuid4

    action_item = ActionItem(
        id=uuid4(),
        meeting_id=test_meeting.id,
        content="To be deleted"
    )
    db_session.add(action_item)
    await db_session.commit()

    response = await auth_client.delete(
        f"/api/v1/meetings/{test_meeting.id}/actions/{action_item.id}"
    )

    assert response.status_code == 204


@pytest.mark.asyncio
async def test_other_user_cannot_access_meeting(client: AsyncClient, test_meeting: Meeting, db_session):
    """Test user cannot access another user's meeting."""
    from app.models.user import User
    from app.core.security import get_password_hash, create_access_token

    # Create another user
    other_user = User(
        id=uuid4(),
        email="other@example.com",
        hashed_password=get_password_hash("password123"),
        name="Other User"
    )
    db_session.add(other_user)
    await db_session.commit()

    # Get token for other user
    other_token = create_access_token(data={"sub": str(other_user.id)})

    # Try to access original user's meeting
    client.headers["Authorization"] = f"Bearer {other_token}"
    response = await client.get(f"/api/v1/meetings/{test_meeting.id}")

    assert response.status_code == 404  # Should not find it


@pytest.mark.asyncio
async def test_get_transcript_not_found(auth_client: AsyncClient, test_meeting: Meeting):
    """Test getting transcript when not generated."""
    response = await auth_client.get(f"/api/v1/meetings/{test_meeting.id}/transcript")

    assert response.status_code == 404
    assert "not yet generated" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_summary_not_found(auth_client: AsyncClient, test_meeting: Meeting):
    """Test getting summary when not generated."""
    response = await auth_client.get(f"/api/v1/meetings/{test_meeting.id}/summary")

    assert response.status_code == 404
    assert "not yet generated" in response.json()["detail"]
