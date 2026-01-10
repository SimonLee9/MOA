# LangGraph Architecture - MOA Meeting Intelligence Platform

> **Version**: 2.0
> **Updated**: 2026-01-10
> **Based on**: 서브 에이전트 및 스킬 설정 가이드

---

## Overview

This document describes the LangGraph-based architecture for the MOA (Minutes of Action) platform, implementing the patterns from the "차세대 AI 에이전트 오케스트레이션" guide.

## Key Features

1. **Tus Protocol** - Resumable uploads for large audio files
2. **PostgreSQL Checkpointer** - Persistent state for long-running workflows
3. **Human-in-the-Loop** - Modern interrupt() pattern for review
4. **MCP Integration** - Extensible action execution via Model Context Protocol
5. **Retry Mechanisms** - Automatic critique-based retry + human feedback retry

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                      CLIENT (Upload)                            │
│                  Tus Protocol (Resumable)                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Gateway                              │
│  - Tus Router (file chunks)                                     │
│  - Process Trigger API                                          │
│  - Review API (HITL)                                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│              LangGraph Processing Pipeline                       │
│                                                                 │
│    STT ──> Summarizer ──> ActionExtractor ──> Critique         │
│             ▲                                      │            │
│             │                                      ▼            │
│             │                              (Pass/Fail?)         │
│             │                                      │            │
│             │                        ┌─────────────┴──────┐    │
│             │                        │                    │    │
│             │                    Pass (or               Fail   │
│             │                   max retry)            (retry<3)│
│             │                        │                    │    │
│             │                        ▼                    ▼    │
│             │               HumanReview ◄────────(retry loop)  │
│             │                        │                         │
│             │                        │                         │
│             │                  (interrupt())                   │
│             │                        │                         │
│             │              ┌─────────┴─────────┐              │
│             │              │                   │              │
│             │           Approve            Reject             │
│             │              │              (feedback)          │
│             │              ▼                   │              │
│             │            Save                  │              │
│             │              │                   │              │
│             └──────────────┴───────────────────┘              │
│                            │                                   │
│                            ▼                                   │
│                           END                                  │
└─────────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                PostgreSQL Checkpointer                          │
│   - Stores workflow state at each step                         │
│   - Enables pause/resume (HITL)                                │
│   - Survives crashes/restarts                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## State Schema

Based on `MeetingAgentState` from the guide:

```python
class MeetingAgentState(TypedDict):
    # Input
    meeting_id: str
    audio_file_url: str
    meeting_title: str
    meeting_date: Optional[str]

    # STT Output
    transcript_segments: List[TranscriptSegment]
    raw_text: str
    speakers: List[str]
    audio_duration: float

    # LLM Outputs
    draft_summary: str
    key_points: List[str]
    decisions: List[str]
    action_items: List[ActionItem]  # With tool_call_payload

    # Quality Control
    critique: str
    critique_issues: List[str]
    critique_passed: bool
    retry_count: int

    # Human-in-the-Loop
    requires_human_review: bool
    human_feedback: Optional[str]
    human_approved: bool

    # Final Output
    final_summary: Optional[str]
    final_key_points: Optional[List[str]]
    final_decisions: Optional[List[str]]
    final_action_items: Optional[List[ActionItem]]

    # Metadata
    status: Literal[...]
    error_message: Optional[str]
    started_at: str
    completed_at: Optional[str]
```

### Enhanced ActionItem Structure

```python
class ActionItem(TypedDict):
    id: str
    content: str
    assignee: Optional[str]
    due_date: Optional[str]
    priority: Literal["low", "medium", "high", "urgent"]

    # NEW: MCP integration
    tool_call_payload: Optional[dict]  # {"tool": "jira_create_issue", "args": {...}}
    status: Literal["pending", "approved", "rejected", "executed"]
```

---

## Node Implementations

### 1. STT Node (Transcriber)

- **Input**: `audio_file_url`
- **Process**: Naver Clova STT with speaker diarization
- **Output**: `transcript_segments`, `raw_text`, `speakers`, `audio_duration`
- **Error Handling**: Sets `status="failed"` on error

### 2. Summarizer Node (Analyst)

- **Input**: `raw_text`, `meeting_title`, `meeting_date`, `speakers`
- **Process**: Claude API for structured summary generation
- **Output**: `draft_summary`, `key_points`, `decisions`
- **Retry Support**: Uses `human_feedback` if available from previous rejection

### 3. Action Extractor Node

- **Input**: `raw_text`, `draft_summary`, `speakers`
- **Process**: Claude API to extract action items
- **Output**: `action_items` (each with `tool_call_payload` mapping)
- **Tool Mapping**: Automatically maps actions to MCP tools (Jira, Calendar, etc.)

### 4. Critique Node

- **Input**: All outputs from Summarizer & ActionExtractor
- **Process**: Self-validation using Claude
- **Output**: `critique`, `critique_issues`, `critique_passed`
- **Routing**:
  - `critique_passed=True` → HumanReview
  - `critique_passed=False` + `retry_count<3` → Summarizer (retry)
  - `retry_count>=3` → HumanReview anyway

### 5. Human Review Node (HITL)

**Implementation** (following the guide):

```python
from langgraph.types import interrupt

async def human_review_node(state: MeetingAgentState) -> dict:
    # Prepare review data
    review_data = {
        "type": "review_request",
        "meeting_id": state["meeting_id"],
        "minutes": state["draft_summary"],
        "key_points": state["key_points"],
        "decisions": state["decisions"],
        "proposed_actions": state["action_items"],
        "critique": state.get("critique", ""),
    }

    # Pause execution until user responds
    user_decision = interrupt(review_data)

    # Process user decision
    if user_decision.get("action") == "approve":
        return {
            "final_summary": user_decision.get("updated_summary", state["draft_summary"]),
            "final_action_items": user_decision.get("updated_actions", state["action_items"]),
            "human_approved": True,
            "status": "approved",
        }
    else:
        return {
            "human_approved": False,
            "human_feedback": user_decision.get("feedback"),
            "status": "revision_requested",
            "retry_count": state.get("retry_count", 0) + 1,
        }
```

**Resume via API**:

```python
from langgraph.types import Command

await graph.ainvoke(
    Command(resume={
        "action": "approve",
        "updated_summary": "...",
        "updated_actions": [...]
    }),
    config={"configurable": {"thread_id": meeting_id}}
)
```

### 6. Save Node

- **Input**: `final_*` fields
- **Process**: Save to database
- **Output**: `status="completed"`, `completed_at`

---

## PostgreSQL Checkpointer

**Purpose**: Enable workflows to pause for hours/days waiting for human review.

**Implementation**:

```python
from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

async def create_checkpointer():
    connection_string = "postgresql+asyncpg://user:pass@host:5432/db"
    checkpointer = AsyncPostgresSaver.from_conn_string(connection_string)
    await checkpointer.setup()  # Creates checkpoint tables
    return checkpointer
```

**Usage**:

```python
checkpointer = await get_checkpointer()
graph = builder.compile(checkpointer=checkpointer)
```

**Benefits**:
- State persists across server restarts
- Supports concurrent meeting processing
- Enables state inspection via `graph.aget_state(config)`

---

## API Endpoints

### 1. Upload & Process

#### POST `/api/v1/upload/files`
- **Protocol**: Tus (resumable upload)
- **Max Size**: 2GB
- **Returns**: File ID

#### POST `/api/v1/upload/meetings/{meeting_id}/process`
- **Params**: `file_id` (from Tus upload)
- **Action**: Triggers LangGraph workflow in background
- **Returns**: `{ "status": "processing_started" }`

### 2. Status Monitoring

#### GET `/api/v1/upload/meetings/{meeting_id}/status`
- **Returns**: Current workflow progress
```json
{
  "meeting_id": "...",
  "status": "pending_review",
  "requires_review": true,
  "progress": {
    "stt_complete": true,
    "summary_complete": true,
    "actions_extracted": true,
    "critique_complete": true
  }
}
```

### 3. Human Review (HITL)

#### GET `/api/v1/meetings/{meeting_id}/review`
- **Returns**: Data to be reviewed
```json
{
  "meeting_id": "...",
  "requires_review": true,
  "review_data": {
    "minutes": "...",
    "key_points": [...],
    "decisions": [...],
    "proposed_actions": [...],
    "critique": "..."
  }
}
```

#### POST `/api/v1/meetings/{meeting_id}/review`
- **Body**:
```json
{
  "action": "approve",  // or "reject"
  "feedback": "Please add more details to decision #2",
  "updated_summary": "...",  // Optional modifications
  "updated_actions": [...]    // Optional modifications
}
```
- **Action**: Resumes workflow with Command(resume=...)

### 4. Results

#### GET `/api/v1/meetings/{meeting_id}/results`
- **Returns**: Final approved results
```json
{
  "meeting_id": "...",
  "status": "completed",
  "summary": "...",
  "key_points": [...],
  "decisions": [...],
  "action_items": [...],
  "execution_results": [...]  // MCP tool execution results
}
```

---

## Retry Mechanisms

### Automatic Retry (Critique-based)

1. Critique Node evaluates quality
2. If `critique_passed=False` and `retry_count<3`:
   - Return to Summarizer
   - Include critique feedback in prompt
   - Increment `retry_count`
3. If `retry_count>=3`: Proceed to HumanReview anyway

### Human Feedback Retry

1. User rejects in HumanReview
2. If `retry_count<5`:
   - Return to Summarizer
   - Include `human_feedback` in prompt
   - Increment `retry_count`
3. If `retry_count>=5`: End workflow with failure

---

## MCP Integration (Executor Node)

**Purpose**: Execute approved action items via external tools.

**Supported Tools** (extensible):
- `jira_create_issue` - Create Jira tickets
- `calendar_create_event` - Schedule meetings
- `email_send` - Send email notifications
- Custom MCP servers

**Flow**:
1. Analyst Node maps actions to tools (`tool_call_payload`)
2. Human approves actions in Review
3. Executor Node calls MCP client for each approved action
4. Results stored in `execution_results`

**Example**:

```python
action_item = {
    "id": "act_1",
    "content": "Create Jira ticket for bug fix",
    "assignee": "john@example.com",
    "tool_call_payload": {
        "tool": "jira_create_issue",
        "args": {
            "project": "PROJ",
            "summary": "Fix authentication bug",
            "assignee": "john@example.com",
            "priority": "high"
        }
    },
    "status": "approved"
}

# After execution
execution_result = {
    "action_id": "act_1",
    "status": "success",
    "result": {
        "issue_key": "PROJ-123",
        "url": "https://jira.example.com/browse/PROJ-123"
    }
}
```

---

## Deployment Considerations

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql+asyncpg://moa:moa@localhost:5432/moa

# Redis (for Celery/background tasks)
REDIS_URL=redis://localhost:6379

# Storage
UPLOAD_DIR=./meeting_uploads

# AI Services
CLOVA_API_KEY=your_clova_key
CLOVA_API_SECRET=your_clova_secret
CLAUDE_API_KEY=your_claude_key

# MCP Servers (optional)
JIRA_MCP_URL=https://mcp.jira.com/v1
CALENDAR_MCP_URL=https://mcp.google.com/calendar
```

### Database Migrations

The PostgreSQL checkpointer creates its own tables automatically:
- `checkpoints` - Stores workflow states
- `checkpoint_metadata` - Metadata for each checkpoint

Ensure the MOA database user has CREATE TABLE permissions.

### Scaling

- **Horizontal**: Multiple FastAPI workers can process different meetings concurrently
- **Vertical**: LangGraph supports streaming for progress updates
- **Isolation**: Each meeting has its own `thread_id` (meeting_id)

---

## Comparison with Guide Architecture

| Feature | Guide | MOA Implementation |
|---------|-------|-------------------|
| Upload | Tus Protocol | ✅ Implemented |
| State Storage | PostgreSQL AsyncSaver | ✅ Implemented |
| HITL | interrupt() + Command | ✅ Implemented |
| Retry Logic | Critique + Human feedback | ✅ Dual retry system |
| MCP Integration | Executor Node | ✅ Placeholder + extensible |
| Checkpointing | Required for HITL | ✅ PostgreSQL-backed |

---

## Next Steps

1. **Implement STT Integration** - Connect Naver Clova API
2. **Implement LLM Prompts** - Complete summarize/extract/critique prompts
3. **MCP Server Connections** - Connect real Jira/Calendar servers
4. **Frontend HITL UI** - Build review approval interface
5. **Monitoring** - Add logging and metrics for workflow steps
6. **Testing** - End-to-end tests for HITL scenarios

---

## References

1. 서브 에이전트 및 스킬 설정 가이드 (provided document)
2. [LangGraph Documentation](https://docs.langchain.com/oss/python/langgraph/)
3. [Tus Protocol](https://tus.io/)
4. [Model Context Protocol](https://modelcontextprotocol.io/)

---

**Document Author**: Claude Sonnet 4.5
**Based on**: 차세대 AI 에이전트 오케스트레이션 가이드
