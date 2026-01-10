"""
Pytest Configuration for AI Pipeline Tests
"""

import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import AsyncMock, MagicMock, patch

from pipeline.state import (
    MeetingAgentState,
    TranscriptSegment,
    ActionItem,
    create_initial_state,
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_meeting_id() -> str:
    """Sample meeting ID."""
    return "test-meeting-123"


@pytest.fixture
def sample_audio_url() -> str:
    """Sample audio file URL."""
    return "https://storage.example.com/audio/test-meeting.wav"


@pytest.fixture
def sample_transcript_segments() -> List[TranscriptSegment]:
    """Sample transcript segments."""
    return [
        {
            "speaker": "김철수",
            "text": "오늘 회의에서는 다음 분기 계획에 대해 논의하겠습니다.",
            "start_time": 0.0,
            "end_time": 5.2,
            "confidence": 0.95,
        },
        {
            "speaker": "이영희",
            "text": "마케팅 팀에서는 신규 캠페인을 3월에 시작할 예정입니다.",
            "start_time": 5.5,
            "end_time": 10.8,
            "confidence": 0.92,
        },
        {
            "speaker": "김철수",
            "text": "좋습니다. 예산은 얼마나 필요하신가요?",
            "start_time": 11.0,
            "end_time": 13.5,
            "confidence": 0.98,
        },
        {
            "speaker": "이영희",
            "text": "약 5천만원 정도 필요합니다. 다음 주까지 상세 계획서를 제출하겠습니다.",
            "start_time": 14.0,
            "end_time": 20.3,
            "confidence": 0.94,
        },
        {
            "speaker": "박지민",
            "text": "개발팀에서도 새 기능 출시 일정을 조율해야 할 것 같습니다.",
            "start_time": 21.0,
            "end_time": 25.5,
            "confidence": 0.91,
        },
    ]


@pytest.fixture
def sample_raw_text(sample_transcript_segments) -> str:
    """Sample raw transcript text."""
    return "\n".join(
        f"{seg['speaker']}: {seg['text']}"
        for seg in sample_transcript_segments
    )


@pytest.fixture
def sample_speakers() -> List[str]:
    """Sample speaker list."""
    return ["김철수", "이영희", "박지민"]


@pytest.fixture
def sample_summary() -> str:
    """Sample meeting summary."""
    return """이번 회의에서는 다음 분기 계획에 대해 논의했습니다.
    마케팅 팀은 3월에 신규 캠페인을 시작할 예정이며, 약 5천만원의 예산이 필요합니다.
    이영희 담당자가 다음 주까지 상세 계획서를 제출하기로 했습니다.
    개발팀에서도 새 기능 출시 일정 조율이 필요한 상황입니다."""


@pytest.fixture
def sample_key_points() -> List[str]:
    """Sample key points."""
    return [
        "다음 분기 계획 논의",
        "마케팅 캠페인 3월 시작 예정",
        "예산 5천만원 필요",
        "상세 계획서 다음 주 제출",
        "개발팀 일정 조율 필요",
    ]


@pytest.fixture
def sample_decisions() -> List[str]:
    """Sample decisions."""
    return [
        "마케팅 캠페인 3월 시작 확정",
        "예산 5천만원 승인",
    ]


@pytest.fixture
def sample_action_items() -> List[ActionItem]:
    """Sample action items."""
    return [
        {
            "id": "action-1",
            "content": "마케팅 캠페인 상세 계획서 제출",
            "assignee": "이영희",
            "due_date": "2024-01-22",
            "priority": "high",
            "tool_call_payload": {
                "tool": "jira_create_issue",
                "args": {
                    "project": "MARKETING",
                    "summary": "마케팅 캠페인 상세 계획서 작성",
                    "assignee": "이영희",
                },
            },
            "status": "pending",
        },
        {
            "id": "action-2",
            "content": "개발팀 일정 조율 회의 진행",
            "assignee": "박지민",
            "due_date": "2024-01-25",
            "priority": "medium",
            "tool_call_payload": {
                "tool": "calendar_create_event",
                "args": {
                    "summary": "개발팀 일정 조율 회의",
                    "start_time": "2024-01-25T14:00:00",
                },
            },
            "status": "pending",
        },
    ]


@pytest.fixture
def initial_state(sample_meeting_id, sample_audio_url) -> MeetingAgentState:
    """Create initial meeting state."""
    return create_initial_state(
        meeting_id=sample_meeting_id,
        audio_file_url=sample_audio_url,
        meeting_title="분기별 계획 회의",
        meeting_date="2024-01-15",
    )


@pytest.fixture
def stt_complete_state(
    initial_state,
    sample_transcript_segments,
    sample_raw_text,
    sample_speakers,
) -> MeetingAgentState:
    """State after STT completion."""
    state = initial_state.copy()
    state.update({
        "transcript_segments": sample_transcript_segments,
        "raw_text": sample_raw_text,
        "speakers": sample_speakers,
        "audio_duration": 25.5,
        "status": "stt_complete",
    })
    return state


@pytest.fixture
def summarized_state(
    stt_complete_state,
    sample_summary,
    sample_key_points,
    sample_decisions,
) -> MeetingAgentState:
    """State after summarization."""
    state = stt_complete_state.copy()
    state.update({
        "draft_summary": sample_summary,
        "key_points": sample_key_points,
        "decisions": sample_decisions,
        "status": "summarized",
    })
    return state


@pytest.fixture
def actions_extracted_state(
    summarized_state,
    sample_action_items,
) -> MeetingAgentState:
    """State after action extraction."""
    state = summarized_state.copy()
    state.update({
        "action_items": sample_action_items,
        "status": "actions_extracted",
    })
    return state


@pytest.fixture
def mock_claude_client():
    """Mock Claude client for testing."""
    with patch("pipeline.integrations.claude_llm.get_claude_client") as mock:
        client = AsyncMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_clova_stt():
    """Mock Clova STT for testing."""
    with patch("pipeline.integrations.clova_stt.ClovaSpeechClient") as mock:
        client = AsyncMock()
        mock.return_value = client
        yield client


@pytest.fixture
def mock_mcp_client():
    """Mock MCP client for testing."""
    with patch("pipeline.integrations.mcp_client.get_mcp_client") as mock:
        client = AsyncMock()
        client.get_available_tools.return_value = []
        client.call_tool.return_value = {"success": True}
        mock.return_value = client
        yield client
