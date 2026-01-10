"""
Meeting Export API
Provides endpoints for exporting meeting data in various formats
"""

from uuid import UUID
from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.meeting import Meeting, MeetingStatus


router = APIRouter(prefix="/export", tags=["Export"])


def generate_markdown(meeting: Meeting) -> str:
    """Generate Markdown content for a meeting"""
    lines = []

    # Title and metadata
    lines.append(f"# {meeting.title}")
    lines.append("")

    if meeting.meeting_date:
        lines.append(f"**회의 일자:** {meeting.meeting_date.strftime('%Y년 %m월 %d일')}")
    lines.append(f"**생성 일시:** {meeting.created_at.strftime('%Y-%m-%d %H:%M')}")
    if meeting.audio_duration:
        minutes = meeting.audio_duration // 60
        seconds = meeting.audio_duration % 60
        lines.append(f"**녹음 길이:** {minutes}분 {seconds}초")
    if meeting.tags:
        lines.append(f"**태그:** {', '.join(meeting.tags)}")
    lines.append("")

    # Summary
    if meeting.summary:
        lines.append("## 회의 요약")
        lines.append("")
        lines.append(meeting.summary.summary)
        lines.append("")

        # Key Points
        if meeting.summary.key_points:
            lines.append("### 핵심 포인트")
            lines.append("")
            for i, point in enumerate(meeting.summary.key_points, 1):
                lines.append(f"{i}. {point}")
            lines.append("")

        # Decisions
        if meeting.summary.decisions:
            lines.append("### 결정 사항")
            lines.append("")
            for decision in meeting.summary.decisions:
                lines.append(f"- {decision}")
            lines.append("")

    # Action Items
    if meeting.action_items:
        lines.append("## 액션 아이템")
        lines.append("")

        for item in meeting.action_items:
            status_emoji = "✅" if item.status.value == "completed" else "⬜"
            priority_labels = {"low": "낮음", "medium": "보통", "high": "높음", "urgent": "긴급"}
            priority = priority_labels.get(item.priority.value, item.priority.value)

            line = f"- {status_emoji} **{item.content}**"
            details = []
            if item.assignee:
                details.append(f"담당: {item.assignee}")
            if item.due_date:
                details.append(f"마감: {item.due_date.strftime('%Y-%m-%d')}")
            details.append(f"우선순위: {priority}")

            if details:
                line += f" ({', '.join(details)})"
            lines.append(line)
        lines.append("")

    # Transcript
    if meeting.transcripts:
        lines.append("## 트랜스크립트")
        lines.append("")

        for segment in meeting.transcripts:
            minutes = int(segment.start_time) // 60
            seconds = int(segment.start_time) % 60
            lines.append(f"**[{minutes:02d}:{seconds:02d}] {segment.speaker}:** {segment.text}")
            lines.append("")

    # Footer
    lines.append("---")
    lines.append(f"*이 문서는 MOA에서 {datetime.now().strftime('%Y-%m-%d %H:%M')}에 생성되었습니다.*")

    return "\n".join(lines)


def generate_html_for_pdf(meeting: Meeting) -> str:
    """Generate HTML content for PDF conversion"""
    html_parts = []

    html_parts.append("""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <style>
        body { font-family: 'Malgun Gothic', sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }
        h1 { color: #1e40af; border-bottom: 2px solid #1e40af; padding-bottom: 10px; }
        h2 { color: #1e3a8a; margin-top: 30px; }
        h3 { color: #374151; margin-top: 20px; }
        .meta { color: #6b7280; font-size: 14px; margin-bottom: 20px; }
        .meta span { margin-right: 20px; }
        .tag { background: #e5e7eb; padding: 2px 8px; border-radius: 4px; font-size: 12px; margin-right: 5px; }
        .summary { background: #f3f4f6; padding: 15px; border-radius: 8px; margin: 15px 0; }
        .key-point { background: #fef3c7; padding: 10px 15px; margin: 5px 0; border-left: 3px solid #f59e0b; }
        .decision { background: #d1fae5; padding: 10px 15px; margin: 5px 0; border-left: 3px solid #10b981; }
        .action-item { padding: 10px; border: 1px solid #e5e7eb; margin: 8px 0; border-radius: 6px; }
        .action-completed { background: #f0fdf4; }
        .action-pending { background: #fffbeb; }
        .priority { font-size: 12px; padding: 2px 6px; border-radius: 4px; }
        .priority-low { background: #e5e7eb; color: #374151; }
        .priority-medium { background: #dbeafe; color: #1e40af; }
        .priority-high { background: #fed7aa; color: #c2410c; }
        .priority-urgent { background: #fee2e2; color: #dc2626; }
        .transcript-segment { margin: 10px 0; padding: 10px; background: #f9fafb; border-radius: 4px; }
        .speaker { font-weight: bold; color: #2563eb; }
        .timestamp { color: #9ca3af; font-size: 12px; }
        .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #e5e7eb; color: #9ca3af; font-size: 12px; text-align: center; }
    </style>
</head>
<body>
""")

    # Title
    html_parts.append(f"<h1>{meeting.title}</h1>")

    # Metadata
    html_parts.append('<div class="meta">')
    if meeting.meeting_date:
        html_parts.append(f'<span>📅 {meeting.meeting_date.strftime("%Y년 %m월 %d일")}</span>')
    if meeting.audio_duration:
        minutes = meeting.audio_duration // 60
        html_parts.append(f'<span>⏱️ {minutes}분</span>')
    html_parts.append('</div>')

    if meeting.tags:
        html_parts.append('<div style="margin-bottom: 20px;">')
        for tag in meeting.tags:
            html_parts.append(f'<span class="tag">{tag}</span>')
        html_parts.append('</div>')

    # Summary
    if meeting.summary:
        html_parts.append('<h2>회의 요약</h2>')
        html_parts.append(f'<div class="summary">{meeting.summary.summary}</div>')

        if meeting.summary.key_points:
            html_parts.append('<h3>핵심 포인트</h3>')
            for i, point in enumerate(meeting.summary.key_points, 1):
                html_parts.append(f'<div class="key-point">{i}. {point}</div>')

        if meeting.summary.decisions:
            html_parts.append('<h3>결정 사항</h3>')
            for decision in meeting.summary.decisions:
                html_parts.append(f'<div class="decision">✓ {decision}</div>')

    # Action Items
    if meeting.action_items:
        html_parts.append('<h2>액션 아이템</h2>')

        priority_classes = {"low": "priority-low", "medium": "priority-medium", "high": "priority-high", "urgent": "priority-urgent"}
        priority_labels = {"low": "낮음", "medium": "보통", "high": "높음", "urgent": "긴급"}

        for item in meeting.action_items:
            status_class = "action-completed" if item.status.value == "completed" else "action-pending"
            status_icon = "✅" if item.status.value == "completed" else "⬜"
            priority_class = priority_classes.get(item.priority.value, "priority-medium")
            priority_label = priority_labels.get(item.priority.value, item.priority.value)

            html_parts.append(f'<div class="action-item {status_class}">')
            html_parts.append(f'<strong>{status_icon} {item.content}</strong><br>')
            html_parts.append(f'<span class="priority {priority_class}">{priority_label}</span>')
            if item.assignee:
                html_parts.append(f' | 담당: {item.assignee}')
            if item.due_date:
                html_parts.append(f' | 마감: {item.due_date.strftime("%Y-%m-%d")}')
            html_parts.append('</div>')

    # Transcript
    if meeting.transcripts:
        html_parts.append('<h2>트랜스크립트</h2>')

        for segment in meeting.transcripts:
            minutes = int(segment.start_time) // 60
            seconds = int(segment.start_time) % 60
            html_parts.append(f'''
                <div class="transcript-segment">
                    <span class="timestamp">[{minutes:02d}:{seconds:02d}]</span>
                    <span class="speaker">{segment.speaker}</span>
                    <p style="margin: 5px 0;">{segment.text}</p>
                </div>
            ''')

    # Footer
    html_parts.append(f'''
        <div class="footer">
            이 문서는 MOA에서 {datetime.now().strftime("%Y-%m-%d %H:%M")}에 생성되었습니다.
        </div>
    </body>
    </html>
    ''')

    return "".join(html_parts)


@router.get("/{meeting_id}/markdown")
async def export_markdown(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export meeting as Markdown file
    """
    result = await db.execute(
        select(Meeting)
        .options(
            selectinload(Meeting.summary),
            selectinload(Meeting.transcripts),
            selectinload(Meeting.action_items),
        )
        .where(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
    )
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )

    markdown_content = generate_markdown(meeting)

    # Create file-like object
    buffer = BytesIO(markdown_content.encode('utf-8'))
    buffer.seek(0)

    filename = f"{meeting.title.replace(' ', '_')}_{meeting.created_at.strftime('%Y%m%d')}.md"

    return StreamingResponse(
        buffer,
        media_type="text/markdown",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/{meeting_id}/html")
async def export_html(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export meeting as HTML file (for PDF printing)
    """
    result = await db.execute(
        select(Meeting)
        .options(
            selectinload(Meeting.summary),
            selectinload(Meeting.transcripts),
            selectinload(Meeting.action_items),
        )
        .where(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
    )
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )

    html_content = generate_html_for_pdf(meeting)

    buffer = BytesIO(html_content.encode('utf-8'))
    buffer.seek(0)

    filename = f"{meeting.title.replace(' ', '_')}_{meeting.created_at.strftime('%Y%m%d')}.html"

    return StreamingResponse(
        buffer,
        media_type="text/html",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )


@router.get("/{meeting_id}/json")
async def export_json(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Export meeting as JSON
    """
    result = await db.execute(
        select(Meeting)
        .options(
            selectinload(Meeting.summary),
            selectinload(Meeting.transcripts),
            selectinload(Meeting.action_items),
        )
        .where(Meeting.id == meeting_id, Meeting.user_id == current_user.id)
    )
    meeting = result.scalar_one_or_none()

    if not meeting:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Meeting not found"
        )

    data = {
        "id": str(meeting.id),
        "title": meeting.title,
        "meeting_date": meeting.meeting_date.isoformat() if meeting.meeting_date else None,
        "audio_duration": meeting.audio_duration,
        "tags": meeting.tags or [],
        "status": meeting.status.value,
        "created_at": meeting.created_at.isoformat(),
        "summary": {
            "text": meeting.summary.summary,
            "key_points": meeting.summary.key_points,
            "decisions": meeting.summary.decisions,
        } if meeting.summary else None,
        "action_items": [
            {
                "content": item.content,
                "assignee": item.assignee,
                "due_date": item.due_date.isoformat() if item.due_date else None,
                "priority": item.priority.value,
                "status": item.status.value,
            }
            for item in meeting.action_items
        ] if meeting.action_items else [],
        "transcripts": [
            {
                "speaker": seg.speaker,
                "text": seg.text,
                "start_time": seg.start_time,
                "end_time": seg.end_time,
            }
            for seg in meeting.transcripts
        ] if meeting.transcripts else [],
    }

    import json
    json_content = json.dumps(data, ensure_ascii=False, indent=2)

    buffer = BytesIO(json_content.encode('utf-8'))
    buffer.seek(0)

    filename = f"{meeting.title.replace(' ', '_')}_{meeting.created_at.strftime('%Y%m%d')}.json"

    return StreamingResponse(
        buffer,
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )
