"""
WebSocket API for real-time progress updates
Provides streaming updates during meeting processing
"""

import asyncio
import json
from typing import Dict, Set
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.meeting import Meeting


router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """
    Manages WebSocket connections for real-time updates

    Features:
    - Track connections per meeting
    - Broadcast progress updates to all subscribers
    - Clean up disconnected clients
    """

    def __init__(self):
        # meeting_id -> set of websocket connections
        self._connections: Dict[str, Set[WebSocket]] = {}
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, meeting_id: str):
        """Accept and register a new connection"""
        await websocket.accept()
        async with self._lock:
            if meeting_id not in self._connections:
                self._connections[meeting_id] = set()
            self._connections[meeting_id].add(websocket)

    async def disconnect(self, websocket: WebSocket, meeting_id: str):
        """Remove a connection"""
        async with self._lock:
            if meeting_id in self._connections:
                self._connections[meeting_id].discard(websocket)
                if not self._connections[meeting_id]:
                    del self._connections[meeting_id]

    async def broadcast(self, meeting_id: str, message: dict):
        """Broadcast a message to all connections for a meeting"""
        async with self._lock:
            if meeting_id not in self._connections:
                return

            disconnected = set()
            for websocket in self._connections[meeting_id]:
                try:
                    await websocket.send_json(message)
                except Exception:
                    disconnected.add(websocket)

            # Clean up disconnected clients
            for ws in disconnected:
                self._connections[meeting_id].discard(ws)

    def get_connection_count(self, meeting_id: str) -> int:
        """Get number of active connections for a meeting"""
        return len(self._connections.get(meeting_id, set()))


# Global connection manager
manager = ConnectionManager()


# Progress update types
class ProgressType:
    UPLOAD = "upload"
    STT_START = "stt_start"
    STT_PROGRESS = "stt_progress"
    STT_COMPLETE = "stt_complete"
    SUMMARIZE_START = "summarize_start"
    SUMMARIZE_COMPLETE = "summarize_complete"
    ACTIONS_START = "actions_start"
    ACTIONS_COMPLETE = "actions_complete"
    CRITIQUE_START = "critique_start"
    CRITIQUE_COMPLETE = "critique_complete"
    REVIEW_PENDING = "review_pending"
    APPROVED = "approved"
    COMPLETED = "completed"
    ERROR = "error"


def create_progress_message(
    progress_type: str,
    progress: int = 0,
    message: str = "",
    data: dict = None,
) -> dict:
    """Create a standardized progress message"""
    return {
        "type": progress_type,
        "progress": progress,
        "message": message,
        "data": data or {},
    }


@router.websocket("/ws/meetings/{meeting_id}/progress")
async def meeting_progress_websocket(
    websocket: WebSocket,
    meeting_id: str,
):
    """
    WebSocket endpoint for real-time meeting processing progress

    Clients connect to this endpoint to receive updates during:
    - Audio upload progress
    - STT processing
    - Summary generation
    - Action item extraction
    - Review status changes

    Message format:
    {
        "type": "stt_progress",
        "progress": 45,
        "message": "Transcribing audio...",
        "data": {}
    }
    """
    await manager.connect(websocket, meeting_id)

    try:
        # Send initial connection confirmation
        await websocket.send_json({
            "type": "connected",
            "meeting_id": meeting_id,
            "message": "Connected to progress stream",
        })

        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for ping or any message from client
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=30.0
                )

                # Handle ping
                if data == "ping":
                    await websocket.send_text("pong")

            except asyncio.TimeoutError:
                # Send keep-alive ping
                try:
                    await websocket.send_json({"type": "ping"})
                except Exception:
                    break

    except WebSocketDisconnect:
        pass
    finally:
        await manager.disconnect(websocket, meeting_id)


async def send_progress_update(
    meeting_id: str,
    progress_type: str,
    progress: int = 0,
    message: str = "",
    data: dict = None,
):
    """
    Send a progress update to all connected clients for a meeting

    This function is called by the pipeline nodes to broadcast progress.

    Args:
        meeting_id: Meeting UUID as string
        progress_type: Type of progress update
        progress: Progress percentage (0-100)
        message: Human-readable status message
        data: Additional data
    """
    update = create_progress_message(progress_type, progress, message, data)
    await manager.broadcast(meeting_id, update)


# === Progress Broadcasting Functions ===
# These are called by pipeline nodes


async def broadcast_stt_start(meeting_id: str):
    """Broadcast STT processing start"""
    await send_progress_update(
        meeting_id,
        ProgressType.STT_START,
        5,
        "음성 인식을 시작합니다...",
    )


async def broadcast_stt_progress(meeting_id: str, progress: int):
    """Broadcast STT progress"""
    await send_progress_update(
        meeting_id,
        ProgressType.STT_PROGRESS,
        5 + int(progress * 0.35),  # 5-40%
        f"음성 인식 중... {progress}%",
    )


async def broadcast_stt_complete(meeting_id: str, duration: float, speaker_count: int):
    """Broadcast STT completion"""
    await send_progress_update(
        meeting_id,
        ProgressType.STT_COMPLETE,
        40,
        f"음성 인식 완료 (발화자 {speaker_count}명 감지)",
        {"duration": duration, "speaker_count": speaker_count},
    )


async def broadcast_summarize_start(meeting_id: str):
    """Broadcast summarization start"""
    await send_progress_update(
        meeting_id,
        ProgressType.SUMMARIZE_START,
        45,
        "AI가 회의 내용을 요약하고 있습니다...",
    )


async def broadcast_summarize_complete(meeting_id: str):
    """Broadcast summarization completion"""
    await send_progress_update(
        meeting_id,
        ProgressType.SUMMARIZE_COMPLETE,
        60,
        "회의 요약 생성 완료",
    )


async def broadcast_actions_start(meeting_id: str):
    """Broadcast action extraction start"""
    await send_progress_update(
        meeting_id,
        ProgressType.ACTIONS_START,
        65,
        "액션 아이템을 추출하고 있습니다...",
    )


async def broadcast_actions_complete(meeting_id: str, action_count: int):
    """Broadcast action extraction completion"""
    await send_progress_update(
        meeting_id,
        ProgressType.ACTIONS_COMPLETE,
        75,
        f"{action_count}개의 액션 아이템 추출 완료",
        {"action_count": action_count},
    )


async def broadcast_critique_start(meeting_id: str):
    """Broadcast critique start"""
    await send_progress_update(
        meeting_id,
        ProgressType.CRITIQUE_START,
        80,
        "결과를 검증하고 있습니다...",
    )


async def broadcast_critique_complete(meeting_id: str, passed: bool, retry_count: int):
    """Broadcast critique completion"""
    if passed:
        await send_progress_update(
            meeting_id,
            ProgressType.CRITIQUE_COMPLETE,
            90,
            "검증 완료, 검토 대기 중",
            {"passed": passed},
        )
    else:
        await send_progress_update(
            meeting_id,
            ProgressType.CRITIQUE_COMPLETE,
            45,  # Go back to summarize
            f"재생성 필요 (시도 {retry_count}/3)",
            {"passed": passed, "retry_count": retry_count},
        )


async def broadcast_review_pending(meeting_id: str):
    """Broadcast review pending status"""
    await send_progress_update(
        meeting_id,
        ProgressType.REVIEW_PENDING,
        95,
        "검토를 기다리고 있습니다...",
    )


async def broadcast_approved(meeting_id: str):
    """Broadcast approval"""
    await send_progress_update(
        meeting_id,
        ProgressType.APPROVED,
        98,
        "승인됨, 결과 저장 중...",
    )


async def broadcast_completed(meeting_id: str):
    """Broadcast completion"""
    await send_progress_update(
        meeting_id,
        ProgressType.COMPLETED,
        100,
        "처리 완료!",
    )


async def broadcast_error(meeting_id: str, error_message: str):
    """Broadcast error"""
    await send_progress_update(
        meeting_id,
        ProgressType.ERROR,
        0,
        f"오류 발생: {error_message}",
        {"error": error_message},
    )
