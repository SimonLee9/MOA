"""
Executor Node
Executes approved action items using MCP tools
"""

from typing import Dict, List, Any
import asyncio


async def executor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Executor Node
    Executes approved action items by calling MCP tools

    This implements the action execution pattern from the guide.
    After human approval, action items with tool_call_payload are executed.

    Flow:
    1. Filter approved action items
    2. Execute each via MCP client
    3. Update action item status
    4. Return execution results

    Args:
        state: Current MeetingAgentState

    Returns:
        Updated state with execution results
    """
    # Get approved action items
    action_items = state.get("final_action_items", [])

    if not action_items:
        return {
            "status": "completed",
            "execution_results": [],
        }

    execution_results = []

    # Execute each action item
    for action in action_items:
        if action.get("status") != "approved":
            continue

        # Check if action has tool call payload
        tool_payload = action.get("tool_call_payload")

        if not tool_payload:
            # No tool to execute, just mark as executed
            action["status"] = "executed"
            execution_results.append({
                "action_id": action.get("id"),
                "status": "skipped",
                "message": "No tool call payload defined",
            })
            continue

        # Execute the tool via MCP
        try:
            result = await execute_mcp_tool(tool_payload)

            action["status"] = "executed"
            execution_results.append({
                "action_id": action.get("id"),
                "status": "success",
                "result": result,
            })

        except Exception as e:
            action["status"] = "failed"
            execution_results.append({
                "action_id": action.get("id"),
                "status": "error",
                "error": str(e),
            })

    return {
        "status": "completed",
        "execution_results": execution_results,
        "final_action_items": action_items,  # Return updated items
    }


async def execute_mcp_tool(tool_payload: Dict[str, Any]) -> Any:
    """
    Execute an MCP tool call

    Uses the MCP client to execute tools on connected servers.
    Falls back to legacy handlers if MCP is not configured.

    Example tool_payload:
    {
        "tool": "jira_create_issue",
        "args": {
            "project": "PROJ",
            "summary": "Action item title",
            "description": "Details...",
            "assignee": "user@example.com"
        }
    }

    Args:
        tool_payload: Tool name and arguments

    Returns:
        Tool execution result
    """
    from pipeline.integrations.mcp_client import execute_tool, get_mcp_client

    tool_name = tool_payload.get("tool")
    args = tool_payload.get("args", {})

    if not tool_name:
        raise ValueError("Tool name is required in tool_call_payload")

    # Check if MCP client has the tool available
    client = get_mcp_client()
    available_tools = client.get_available_tools()
    available_tool_names = [t.name for t in available_tools]

    # If MCP is configured for this tool, use MCP client
    if tool_name in available_tool_names:
        return await execute_tool(tool_name, args)

    # Fallback to legacy handlers for backward compatibility
    if tool_name == "jira_create_issue":
        return await create_jira_issue(args)
    elif tool_name == "calendar_create_event":
        return await create_calendar_event(args)
    else:
        raise ValueError(f"Unknown tool and no MCP server configured: {tool_name}")


# === MCP Tool Implementations ===
# These are placeholders - in production, use actual MCP clients


async def create_jira_issue(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a Jira issue via MCP

    In production, this would use:
    - MCP Jira server (from the guide references)
    - mcp_client.call_tool("jira_create_issue", args)
    """
    # Simulate API call
    await asyncio.sleep(0.1)

    return {
        "issue_key": "PROJ-123",
        "url": f"https://jira.example.com/browse/PROJ-123",
        "status": "created",
    }


async def create_calendar_event(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a calendar event via MCP

    In production, this would use:
    - Google Calendar MCP server (from the guide references)
    - mcp_client.call_tool("calendar_create_event", args)
    """
    # Simulate API call
    await asyncio.sleep(0.1)

    return {
        "event_id": "evt_abc123",
        "url": "https://calendar.google.com/event?eid=evt_abc123",
        "status": "created",
    }


# === Helper Functions ===


def map_action_to_tool(action_item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map an action item to an MCP tool call payload

    This function analyzes the action item and determines which tool to use.
    It's called by the Analyst node when extracting action items.

    Examples:
    - "Send email to John" -> email_send tool
    - "Create Jira ticket for bug fix" -> jira_create_issue tool
    - "Schedule meeting next week" -> calendar_create_event tool

    Args:
        action_item: ActionItem dict

    Returns:
        Tool call payload or None if no tool needed
    """
    content = action_item.get("content", "").lower()

    # Simple keyword matching (in production, use LLM to classify)
    if "jira" in content or "ticket" in content or "issue" in content:
        return {
            "tool": "jira_create_issue",
            "args": {
                "project": "MEETING",
                "summary": action_item.get("content"),
                "assignee": action_item.get("assignee"),
                "priority": action_item.get("priority", "medium"),
            }
        }

    elif "meeting" in content or "schedule" in content or "calendar" in content:
        return {
            "tool": "calendar_create_event",
            "args": {
                "summary": action_item.get("content"),
                "attendees": [action_item.get("assignee")] if action_item.get("assignee") else [],
                "due_date": action_item.get("due_date"),
            }
        }

    # No tool mapping found
    return None
