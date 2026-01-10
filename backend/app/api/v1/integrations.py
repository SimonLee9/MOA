"""
External Integrations API
Manages connections to external services (Slack, Google Calendar, etc.)
"""

from uuid import UUID
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.services.slack_service import slack_service
from app.services.google_calendar_service import google_calendar_service, CalendarEvent
from app.config import settings


router = APIRouter(prefix="/integrations", tags=["Integrations"])


# Pydantic Schemas
class SlackTestRequest(BaseModel):
    message: Optional[str] = "MOA 연동 테스트 메시지입니다."


class SlackTestResponse(BaseModel):
    success: bool
    message: str


class IntegrationStatus(BaseModel):
    slack: bool
    google_calendar: bool
    notion: bool
    jira: bool


class IntegrationDetails(BaseModel):
    """Detailed integration status"""
    name: str
    enabled: bool
    configured: bool
    description: str
    required_for: list[str]


class AllIntegrationsResponse(BaseModel):
    """Response with all integration details"""
    integrations: list[IntegrationDetails]


# Endpoints
@router.get("/status", response_model=IntegrationStatus)
async def get_integration_status(
    current_user: User = Depends(get_current_user),
):
    """
    Get the status of all external integrations
    """
    return IntegrationStatus(
        slack=slack_service.enabled,
        google_calendar=google_calendar_service.enabled,
        notion=bool(settings.notion_api_key),
        jira=bool(settings.jira_url and settings.jira_api_token),
    )


@router.get("/details", response_model=AllIntegrationsResponse)
async def get_integration_details(
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed status of all integrations
    """
    services = settings.check_optional_services()

    integrations = [
        IntegrationDetails(
            name="Slack",
            enabled=slack_service.enabled,
            configured=services.get("slack", {}).get("configured", False),
            description="Slack 알림 및 메시지 전송",
            required_for=services.get("slack", {}).get("required_for", []),
        ),
        IntegrationDetails(
            name="Google Calendar",
            enabled=google_calendar_service.enabled,
            configured=services.get("google_calendar", {}).get("configured", False),
            description="Google 캘린더 일정 생성",
            required_for=services.get("google_calendar", {}).get("required_for", []),
        ),
        IntegrationDetails(
            name="Notion",
            enabled=bool(settings.notion_api_key),
            configured=services.get("notion", {}).get("configured", False),
            description="Notion 페이지 생성 및 문서화",
            required_for=services.get("notion", {}).get("required_for", []),
        ),
        IntegrationDetails(
            name="Jira",
            enabled=bool(settings.jira_url and settings.jira_api_token),
            configured=services.get("jira", {}).get("configured", False),
            description="Jira 이슈 생성 및 관리",
            required_for=services.get("jira", {}).get("required_for", []),
        ),
    ]

    return AllIntegrationsResponse(integrations=integrations)


@router.post("/slack/test", response_model=SlackTestResponse)
async def test_slack_integration(
    request: SlackTestRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Test Slack integration by sending a test message
    """
    if not slack_service.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Slack integration is not configured"
        )

    success = await slack_service.send_message(
        text=request.message,
        username="MOA",
        icon_emoji=":test_tube:",
    )

    if success:
        return SlackTestResponse(
            success=True,
            message="테스트 메시지가 성공적으로 전송되었습니다."
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Slack 메시지 전송에 실패했습니다."
        )


@router.post("/slack/notify/review/{meeting_id}")
async def send_slack_review_notification(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a Slack notification for meeting review
    """
    from sqlalchemy import select
    from app.models.meeting import Meeting

    # Get meeting
    result = await db.execute(
        select(Meeting).where(
            Meeting.id == meeting_id,
            Meeting.user_id == current_user.id
        )
    )
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )

    if not slack_service.enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Slack integration is not configured"
        )

    # Build meeting URL (would need to be configured properly)
    meeting_url = f"https://your-domain.com/meetings/{meeting_id}"

    success = await slack_service.send_review_notification(
        meeting_title=meeting.title,
        meeting_id=str(meeting_id),
        meeting_url=meeting_url,
    )

    if success:
        return {"message": "Slack 알림이 전송되었습니다."}
    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Slack 알림 전송에 실패했습니다."
        )


# Google Calendar Integration (Placeholder)
class CalendarEventRequest(BaseModel):
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    attendees: Optional[list[str]] = None


@router.post("/google-calendar/event")
async def create_calendar_event(
    request: CalendarEventRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Create a Google Calendar event (placeholder)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Google Calendar integration is not yet implemented"
    )


# Notion Integration (Placeholder)
class NotionPageRequest(BaseModel):
    meeting_id: UUID
    template: Optional[str] = "default"


@router.post("/notion/page")
async def create_notion_page(
    request: NotionPageRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Create a Notion page from meeting (placeholder)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Notion integration is not yet implemented"
    )


# Jira Integration (Placeholder)
class JiraIssueRequest(BaseModel):
    meeting_id: UUID
    action_item_id: UUID
    project_key: str


@router.post("/jira/issue")
async def create_jira_issue(
    request: JiraIssueRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Create a Jira issue from action item (placeholder)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Jira integration is not yet implemented"
    )
