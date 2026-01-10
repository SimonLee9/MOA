# Changelog - MOA Platform

## [2.0.0] - 2026-01-10

### Major Architecture Overhaul
Based on "서브 에이전트 및 스킬 설정 가이드" recommendations

### Added

#### 1. Tus Protocol for Resumable Uploads
- **File**: `backend/app/api/v1/tus_upload.py`
- **Features**:
  - Chunked upload support for large audio files (up to 2GB)
  - Automatic resume after network failures
  - Background task triggering for LangGraph workflow

#### 2. PostgreSQL Checkpointer for LangGraph
- **File**: `ai_pipeline/pipeline/checkpointer.py`
- **Features**:
  - Persistent state storage using `AsyncPostgresSaver`
  - Enables multi-hour/multi-day workflows
  - Automatic checkpoint table creation
  - Thread-based state isolation (one per meeting)

#### 3. Modern Human-in-the-Loop Pattern
- **File**: `ai_pipeline/pipeline/graph.py` (human_review_node)
- **Features**:
  - Uses `interrupt()` function from LangGraph
  - Pauses workflow execution at review step
  - Resumes with `Command(resume=...)` API
  - Supports user modifications to summary and actions

#### 4. Enhanced Action Item Structure
- **File**: `ai_pipeline/pipeline/state.py`
- **Features**:
  - Added `tool_call_payload` field for MCP integration
  - Added `status` field (pending/approved/rejected/executed)
  - Ready for external tool execution

#### 5. Dual Retry Mechanism
- **Automatic Retry**: Based on critique node (max 3 retries)
- **Human Feedback Retry**: When user rejects (max 5 retries)
- **Routing**: Improved conditional edges in graph

#### 6. MCP Executor Node
- **File**: `ai_pipeline/pipeline/nodes/executor_node.py`
- **Features**:
  - Executes approved action items
  - Supports Jira, Google Calendar, Email tools
  - Extensible for custom MCP servers
  - Returns execution results

#### 7. Human Review API Endpoints
- **File**: `backend/app/api/v1/review.py`
- **Endpoints**:
  - `GET /api/v1/meetings/{id}/review` - Get review data
  - `POST /api/v1/meetings/{id}/review` - Submit approval/rejection
  - `GET /api/v1/meetings/{id}/results` - Get final results
  - Integrated with LangGraph state management

### Changed

#### 1. LangGraph Workflow
- **Before**: Simple linear flow with interrupt_before
- **After**:
  - Complex routing with retry loops
  - In-node interrupt() pattern
  - Human feedback incorporated into retry

#### 2. Graph Compilation
- **Before**: `MemorySaver()` (non-persistent)
- **After**: `AsyncPostgresSaver` (PostgreSQL-backed)

#### 3. Resume Function
- **Before**: Simple state update
- **After**: Uses `Command(resume=...)` to pass data to interrupt()

#### 4. API Router
- **File**: `backend/app/api/v1/router.py`
- Added Tus upload router
- Added review router

### Updated

#### Dependencies
- **File**: `backend/requirements.txt`
- Added: `fastapi-tusd==0.1.0`
- Added: `langgraph==0.2.45`
- Added: `langchain==0.3.7`
- Added: `langchain-anthropic==0.3.0`

### Documentation

#### New Documents
1. **LANGGRAPH_ARCHITECTURE.md**
   - Comprehensive architecture guide
   - Detailed node implementations
   - API endpoint specifications
   - MCP integration patterns
   - Deployment considerations

### Technical Highlights

#### State Management
```python
# Thread-based isolation
config = {"configurable": {"thread_id": meeting_id}}

# Persistent checkpointing
checkpointer = await get_checkpointer()
graph = builder.compile(checkpointer=checkpointer)
```

#### Human-in-the-Loop
```python
# Pause execution
user_decision = interrupt(review_data)

# Resume with user input
await graph.ainvoke(Command(resume=decision), config)
```

#### Retry Loops
- **Critique Loop**: STT → Summarizer → Extract → Critique → (retry if failed)
- **Human Loop**: HumanReview → (retry to Summarizer if rejected)

### Migration Guide

#### For Developers

1. **Install new dependencies**:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Update database connection**:
   - Ensure `DATABASE_URL` uses `postgresql+asyncpg://` format
   - Checkpointer will auto-create tables on first run

3. **Environment variables**:
   - Add `UPLOAD_DIR` for Tus uploads
   - Existing variables unchanged

#### For API Clients

1. **Upload flow change**:
   - **Old**: POST file directly to `/api/v1/meetings/{id}/upload`
   - **New**: Use Tus protocol via `/api/v1/upload/files` then trigger `/api/v1/upload/meetings/{id}/process`

2. **Review flow**:
   - Poll `/api/v1/meetings/{id}/review` for review requests
   - Submit decisions to `/api/v1/meetings/{id}/review`
   - Retrieve final results from `/api/v1/meetings/{id}/results`

### Breaking Changes

⚠️ **Upload API**
- Old upload endpoint still exists but Tus is recommended for large files

⚠️ **Graph Configuration**
- `create_meeting_graph()` is now async (must be awaited)
- Returns graph with PostgreSQL checkpointer instead of MemorySaver

### Future Work

- [x] ~~Implement actual STT integration (Naver Clova)~~ - Completed
- [x] ~~Complete LLM prompts for summarizer/extractor/critique~~ - Completed
- [x] ~~Connect real MCP servers (Jira, Google Calendar)~~ - Completed
- [x] ~~Build frontend HITL review UI~~ - Completed
- [x] ~~Add streaming support for progress updates~~ - Completed
- [x] ~~Implement workflow monitoring and metrics~~ - Completed

---

## [2.1.0] - 2026-01-10

### Completed All MVP Features

#### Frontend HITL Review UI
- **File**: `frontend/components/review/ReviewPanel.tsx`
- **Features**:
  - Full review panel for AI-generated content
  - Editable summary, key points, decisions
  - Action items management (add/edit/remove)
  - Approve/Reject workflow with feedback
  - Real-time status updates

#### MCP Client Integration
- **File**: `ai_pipeline/pipeline/integrations/mcp_client.py`
- **Features**:
  - Configurable MCP server connections
  - Support for Jira, Google Calendar, Notion, Slack
  - Tool registry with validation
  - Fallback handlers for non-MCP execution

#### WebSocket Progress Streaming
- **File**: `backend/app/api/v1/websocket.py`
- **Features**:
  - Real-time progress updates via WebSocket
  - Connection manager for multiple clients
  - Step-by-step progress tracking (STT, Summarize, Extract, Critique, Review)
  - Auto-reconnect support

- **File**: `frontend/lib/useProgress.ts`
- **Features**:
  - React hook for WebSocket connection
  - Automatic reconnection logic
  - Progress state management
  - Event callbacks (onComplete, onReviewPending)

- **File**: `frontend/components/meeting/ProgressTracker.tsx`
- **Features**:
  - Visual progress indicator
  - Step-by-step status display
  - Recent updates log

#### Metrics and Monitoring API
- **File**: `backend/app/api/v1/metrics.py`
- **Endpoints**:
  - `GET /api/v1/metrics/health` - System health check
  - `GET /api/v1/metrics/workflows` - Workflow statistics
  - `GET /api/v1/metrics/daily` - Daily meeting counts
  - `GET /api/v1/metrics/user` - User-specific metrics
  - `GET /api/v1/metrics/pipeline/status` - Active processing status

### Updated Files

- `frontend/types/meeting.ts` - Added review types
- `frontend/lib/api.ts` - Added review API client
- `frontend/app/meetings/[id]/page.tsx` - Integrated review and progress UI
- `backend/app/api/v1/router.py` - Added websocket and metrics routers
- `ai_pipeline/pipeline/nodes/executor_node.py` - Integrated MCP client
- `.env.example` - Added MCP configuration variables

### Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                     FRONTEND (Next.js)                       │
├─────────────────────────────────────────────────────────────┤
│  Upload → Progress Tracker → Review Panel → Results View    │
│                    ↑                ↓                        │
│              WebSocket         REST API                      │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                     BACKEND (FastAPI)                        │
├─────────────────────────────────────────────────────────────┤
│  Meetings API │ Review API │ WebSocket │ Metrics API        │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                   AI PIPELINE (LangGraph)                    │
├─────────────────────────────────────────────────────────────┤
│  STT Node → Summarizer → Extractor → Critique → HITL → Save │
│      │                                            │          │
│      └──────────── PostgreSQL Checkpointer ───────┘          │
│                          │                                   │
│                    MCP Client (optional)                     │
│            ┌────────────────────────────┐                    │
│            │ Jira │ Calendar │ Slack    │                    │
│            └────────────────────────────┘                    │
└─────────────────────────────────────────────────────────────┘
```

---

## [1.0.0] - 2025-01-10

Initial release with basic meeting processing pipeline.
