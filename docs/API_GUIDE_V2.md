# MOA API Guide v2.0

> **Version**: 2.0.0
> **Updated**: 2026-01-10
> **New Features**: Tus Upload, Human Review, MCP Integration

---

## Overview

This guide covers the v2.0 API endpoints for the MOA platform, including:
- Resumable file uploads (Tus Protocol)
- LangGraph workflow triggering
- Human-in-the-loop review
- Meeting results retrieval

---

## 1. Resumable Upload (Tus Protocol)

### 1.1 Upload Audio File

**Endpoint**: `POST /api/v1/upload/files`

**Protocol**: [Tus](https://tus.io/) - Resumable Upload Protocol

**Features**:
- Supports files up to 2GB
- Automatic resume after network failures
- Chunked upload for large files

**Client Example** (using tus-js-client):

```javascript
import * as tus from "tus-js-client";

const file = document.getElementById("audio-input").files[0];

const upload = new tus.Upload(file, {
  endpoint: "http://localhost:8000/api/v1/upload/files",
  retryDelays: [0, 3000, 5000, 10000],
  metadata: {
    filename: file.name,
    filetype: file.type,
  },
  onError: (error) => {
    console.error("Upload failed:", error);
  },
  onProgress: (bytesUploaded, bytesTotal) => {
    const percentage = ((bytesUploaded / bytesTotal) * 100).toFixed(2);
    console.log(`Upload progress: ${percentage}%`);
  },
  onSuccess: () => {
    console.log("Upload complete! File ID:", upload.url.split("/").pop());
  },
});

upload.start();
```

**Response**:
```json
{
  "file_id": "abc123def456",
  "location": "/api/v1/upload/files/abc123def456"
}
```

---

## 2. Meeting Processing

### 2.1 Start Processing

**Endpoint**: `POST /api/v1/upload/meetings/{meeting_id}/process`

**Description**: Triggers LangGraph workflow for a meeting

**Request**:
```http
POST /api/v1/upload/meetings/550e8400-e29b-41d4-a716-446655440000/process
Authorization: Bearer <token>
Content-Type: application/json

{
  "file_id": "abc123def456"
}
```

**Response**:
```json
{
  "meeting_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing_started",
  "file_size": 52428800,
  "message": "AI processing has been started. Check the meeting status endpoint for progress."
}
```

### 2.2 Check Processing Status

**Endpoint**: `GET /api/v1/upload/meetings/{meeting_id}/status`

**Description**: Get current workflow progress

**Request**:
```http
GET /api/v1/upload/meetings/550e8400.../status
Authorization: Bearer <token>
```

**Response**:
```json
{
  "meeting_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending_review",
  "requires_review": true,
  "progress": {
    "stt_complete": true,
    "summary_complete": true,
    "actions_extracted": true,
    "critique_complete": true
  },
  "error": null
}
```

**Status Values**:
- `started` - Workflow initiated
- `stt_complete` - Transcription finished
- `summarized` - Summary generated
- `actions_extracted` - Action items extracted
- `critique_complete` - Quality check done
- `pending_review` - Waiting for human approval
- `approved` - User approved
- `completed` - Fully processed
- `failed` - Error occurred

---

## 3. Human Review (HITL)

### 3.1 Get Review Data

**Endpoint**: `GET /api/v1/meetings/{meeting_id}/review`

**Description**: Retrieve data that needs human review

**Request**:
```http
GET /api/v1/meetings/550e8400.../review
Authorization: Bearer <token>
```

**Response**:
```json
{
  "meeting_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending_review",
  "requires_review": true,
  "review_data": {
    "minutes": "이번 회의에서는 2025년 1분기 마케팅 전략과 신규 제품 출시 일정에 대해 논의했습니다...",
    "key_points": [
      "마케팅 예산 20% 증액 합의",
      "신제품 출시일 3월 15일 확정",
      "파트너사 미팅 다음 주 진행 예정"
    ],
    "decisions": [
      "디지털 마케팅 예산을 기존 대비 20% 증액한다",
      "신제품 베타 테스트를 2월 말까지 완료한다"
    ],
    "proposed_actions": [
      {
        "id": "act_1",
        "content": "파트너사 미팅 일정 잡기",
        "assignee": "박 대리",
        "due_date": "2025-01-17",
        "priority": "high",
        "tool_call_payload": {
          "tool": "calendar_create_event",
          "args": {
            "summary": "파트너사 미팅",
            "attendees": ["박 대리"]
          }
        },
        "status": "pending"
      },
      {
        "id": "act_2",
        "content": "마케팅 예산 증액 품의서 작성",
        "assignee": "김 부장",
        "due_date": "2025-01-15",
        "priority": "urgent",
        "tool_call_payload": {
          "tool": "jira_create_issue",
          "args": {
            "project": "MEETING",
            "summary": "마케팅 예산 증액 품의서 작성",
            "assignee": "김 부장",
            "priority": "urgent"
          }
        },
        "status": "pending"
      }
    ],
    "critique": "요약이 명확하고 액션 아이템이 구체적입니다.",
    "retry_count": 0
  }
}
```

### 3.2 Submit Review Decision

**Endpoint**: `POST /api/v1/meetings/{meeting_id}/review`

**Description**: Approve or reject the meeting results

#### 3.2.1 Approve (with modifications)

**Request**:
```http
POST /api/v1/meetings/550e8400.../review
Authorization: Bearer <token>
Content-Type: application/json

{
  "action": "approve",
  "feedback": "Looks good!",
  "updated_summary": "이번 회의에서는 2025년 1분기 마케팅 전략에 대해 논의했습니다...",
  "updated_actions": [
    {
      "id": "act_1",
      "content": "파트너사 미팅 일정 잡기",
      "assignee": "박 대리",
      "due_date": "2025-01-20",
      "priority": "high",
      "status": "approved"
    },
    {
      "id": "act_2",
      "content": "마케팅 예산 증액 품의서 작성",
      "assignee": "김 부장",
      "due_date": "2025-01-15",
      "priority": "urgent",
      "status": "approved"
    }
  ]
}
```

**Response**:
```json
{
  "meeting_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "action": "approve",
  "message": "Review approved successfully. Workflow resumed."
}
```

#### 3.2.2 Reject (request revision)

**Request**:
```http
POST /api/v1/meetings/550e8400.../review
Authorization: Bearer <token>
Content-Type: application/json

{
  "action": "reject",
  "feedback": "액션 아이템 #2의 담당자가 잘못되었습니다. 이 부장님이 맡아야 합니다."
}
```

**Response**:
```json
{
  "meeting_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "action": "reject",
  "message": "Review rejected successfully. Workflow resumed with feedback."
}
```

**Note**: After rejection, the workflow returns to the Summarizer node with human feedback, and will re-generate results (up to 5 retries).

---

## 4. Meeting Results

### 4.1 Get Final Results

**Endpoint**: `GET /api/v1/meetings/{meeting_id}/results`

**Description**: Retrieve approved and completed meeting results

**Request**:
```http
GET /api/v1/meetings/550e8400.../results
Authorization: Bearer <token>
```

**Response**:
```json
{
  "meeting_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "summary": "이번 회의에서는 2025년 1분기 마케팅 전략과 신규 제품 출시 일정에 대해 논의했습니다...",
  "key_points": [
    "마케팅 예산 20% 증액 합의",
    "신제품 출시일 3월 15일 확정",
    "파트너사 미팅 다음 주 진행 예정"
  ],
  "decisions": [
    "디지털 마케팅 예산을 기존 대비 20% 증액한다",
    "신제품 베타 테스트를 2월 말까지 완료한다"
  ],
  "action_items": [
    {
      "id": "act_1",
      "content": "파트너사 미팅 일정 잡기",
      "assignee": "박 대리",
      "due_date": "2025-01-20",
      "priority": "high",
      "tool_call_payload": { ... },
      "status": "executed"
    },
    {
      "id": "act_2",
      "content": "마케팅 예산 증액 품의서 작성",
      "assignee": "김 부장",
      "due_date": "2025-01-15",
      "priority": "urgent",
      "tool_call_payload": { ... },
      "status": "executed"
    }
  ],
  "execution_results": [
    {
      "action_id": "act_1",
      "status": "success",
      "result": {
        "event_id": "evt_abc123",
        "url": "https://calendar.google.com/event?eid=evt_abc123"
      }
    },
    {
      "action_id": "act_2",
      "status": "success",
      "result": {
        "issue_key": "PROJ-123",
        "url": "https://jira.example.com/browse/PROJ-123"
      }
    }
  ],
  "human_approved": true,
  "completed_at": "2025-01-10T16:30:00Z"
}
```

**Error Response** (if not completed):
```json
{
  "detail": "Meeting not completed yet. Current status: pending_review"
}
```

---

## 5. Workflow Diagram

```
Client Upload (Tus)
    │
    ▼
POST /upload/files
    │
    ▼
POST /upload/meetings/{id}/process
    │
    ▼
[LangGraph Workflow Starts]
    │
    ├─ STT
    ├─ Summarizer
    ├─ Action Extractor
    ├─ Critique (auto retry if needed)
    │
    ▼
GET /meetings/{id}/review  ◄─── Poll for review request
    │
    ▼
POST /meetings/{id}/review  ◄─── User approves/rejects
    │
    ├─ If approved: Execute actions (MCP)
    ├─ If rejected: Retry with feedback
    │
    ▼
GET /meetings/{id}/results  ◄─── Get final data
```

---

## 6. Error Handling

### 6.1 Common Error Codes

| Status Code | Meaning | Action |
|-------------|---------|--------|
| 400 | Bad Request | Check request body format |
| 401 | Unauthorized | Provide valid auth token |
| 404 | Not Found | Verify meeting_id exists |
| 413 | File Too Large | File exceeds 2GB limit |
| 500 | Internal Error | Contact support |

### 6.2 Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## 7. Rate Limits

| Endpoint | Limit |
|----------|-------|
| File Upload | 10 concurrent uploads per user |
| Processing | 5 concurrent meetings per user |
| Review APIs | 100 requests/minute |

---

## 8. Changelog

### v2.0.0 (2026-01-10)
- ✅ Added Tus protocol for resumable uploads
- ✅ Added Human Review endpoints
- ✅ Added PostgreSQL checkpointing
- ✅ Added MCP action execution
- ✅ Enhanced workflow status tracking

### v1.0.0 (2025-01-10)
- Initial release

---

## 9. Client Libraries

### JavaScript/TypeScript
```bash
npm install tus-js-client
```

### Python
```bash
pip install tuspy
```

### Flutter
```bash
flutter pub add flutter_chunked_upload
```

---

**For detailed architecture information, see [LANGGRAPH_ARCHITECTURE.md](./LANGGRAPH_ARCHITECTURE.md)**
