"""
Metrics API Tests
"""

import pytest
from uuid import uuid4
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient
from datetime import datetime, timedelta

from app.models.meeting import Meeting, MeetingStatus


@pytest.mark.asyncio
async def test_health_check_healthy(client: AsyncClient, db_session):
    """Test health check when all services are healthy."""
    with patch("app.api.v1.metrics.redis.asyncio") as mock_redis, \
         patch("app.api.v1.metrics.get_checkpointer") as mock_checkpointer, \
         patch("app.api.v1.metrics.get_settings") as mock_settings:

        # Mock Redis
        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping.return_value = True
        mock_redis.from_url.return_value = mock_redis_instance

        # Mock Settings
        mock_settings.return_value.redis_url = "redis://localhost:6379"

        # Mock checkpointer
        mock_checkpointer.return_value = AsyncMock()

        response = await client.get("/api/v1/metrics/health")

        assert response.status_code == 200
        data = response.json()
        assert data["database"] == "healthy"
        assert "timestamp" in data


@pytest.mark.asyncio
async def test_health_check_redis_unhealthy(client: AsyncClient, db_session):
    """Test health check when Redis is unhealthy."""
    with patch("app.api.v1.metrics.redis.asyncio") as mock_redis, \
         patch("app.api.v1.metrics.get_checkpointer") as mock_checkpointer, \
         patch("app.api.v1.metrics.get_settings") as mock_settings:

        # Mock Redis failure
        mock_redis.from_url.side_effect = Exception("Connection refused")

        # Mock Settings
        mock_settings.return_value.redis_url = "redis://localhost:6379"

        # Mock checkpointer
        mock_checkpointer.return_value = AsyncMock()

        response = await client.get("/api/v1/metrics/health")

        assert response.status_code == 200
        data = response.json()
        assert "unhealthy" in data["redis"]


@pytest.mark.asyncio
async def test_workflow_metrics(auth_client: AsyncClient, test_meeting: Meeting, completed_meeting: Meeting):
    """Test workflow metrics retrieval."""
    response = await auth_client.get("/api/v1/metrics/workflows")

    assert response.status_code == 200
    data = response.json()
    assert "total_meetings" in data
    assert "processing" in data
    assert "completed" in data
    assert "failed" in data
    assert "success_rate" in data


@pytest.mark.asyncio
async def test_workflow_metrics_unauthenticated(client: AsyncClient):
    """Test workflow metrics requires authentication."""
    response = await client.get("/api/v1/metrics/workflows")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_daily_stats(auth_client: AsyncClient, test_meeting: Meeting):
    """Test daily statistics retrieval."""
    response = await auth_client.get("/api/v1/metrics/daily?days=7")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 7

    # Each day should have required fields
    for day in data:
        assert "date" in day
        assert "meetings_created" in day
        assert "meetings_completed" in day
        assert "meetings_failed" in day


@pytest.mark.asyncio
async def test_daily_stats_custom_days(auth_client: AsyncClient):
    """Test daily stats with custom day count."""
    response = await auth_client.get("/api/v1/metrics/daily?days=14")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 14


@pytest.mark.asyncio
async def test_user_metrics(auth_client: AsyncClient, test_meeting: Meeting, completed_meeting: Meeting):
    """Test user metrics retrieval."""
    response = await auth_client.get("/api/v1/metrics/user")

    assert response.status_code == 200
    data = response.json()
    assert "total_meetings" in data
    assert "completed_meetings" in data
    assert "pending_review" in data
    assert "total_action_items" in data


@pytest.mark.asyncio
async def test_user_metrics_unauthenticated(client: AsyncClient):
    """Test user metrics requires authentication."""
    response = await client.get("/api/v1/metrics/user")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_pipeline_status(auth_client: AsyncClient, processing_meeting: Meeting):
    """Test pipeline status retrieval."""
    response = await auth_client.get("/api/v1/metrics/pipeline/status")

    assert response.status_code == 200
    data = response.json()
    assert "active_count" in data
    assert "meetings" in data
    assert data["active_count"] >= 1


@pytest.mark.asyncio
async def test_pipeline_status_no_processing(auth_client: AsyncClient, test_meeting: Meeting):
    """Test pipeline status with no processing meetings."""
    # test_meeting is in uploaded status, not processing
    response = await auth_client.get("/api/v1/metrics/pipeline/status")

    assert response.status_code == 200
    data = response.json()
    assert data["active_count"] == 0
    assert len(data["meetings"]) == 0


@pytest.mark.asyncio
async def test_workflow_metrics_success_rate_calculation(
    auth_client: AsyncClient,
    db_session,
    test_user
):
    """Test success rate calculation."""
    # Create meetings with different statuses
    from uuid import uuid4

    # 2 completed
    for _ in range(2):
        meeting = Meeting(
            id=uuid4(),
            user_id=test_user.id,
            title="Completed",
            status=MeetingStatus.COMPLETED,
        )
        db_session.add(meeting)

    # 1 failed
    failed = Meeting(
        id=uuid4(),
        user_id=test_user.id,
        title="Failed",
        status=MeetingStatus.FAILED,
    )
    db_session.add(failed)

    await db_session.commit()

    response = await auth_client.get("/api/v1/metrics/workflows")
    data = response.json()

    # 2 completed out of 3 finished = 66.67%
    assert data["completed"] >= 2
    assert data["failed"] >= 1
    # Success rate should be around 66.67%
    assert data["success_rate"] > 60
