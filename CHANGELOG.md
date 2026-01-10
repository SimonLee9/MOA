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

- [ ] Implement actual STT integration (Naver Clova)
- [ ] Complete LLM prompts for summarizer/extractor/critique
- [ ] Connect real MCP servers (Jira, Google Calendar)
- [ ] Build frontend HITL review UI
- [ ] Add streaming support for progress updates
- [ ] Implement workflow monitoring and metrics

---

## [1.0.0] - 2025-01-10

Initial release with basic meeting processing pipeline.
